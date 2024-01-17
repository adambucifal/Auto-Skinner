import maya.cmds as cmds


class AutoSkinner:
    def __init__(self):
        """
        Creates the main UI for the Auto Skinner.
        :param: None
        :return: None
        """
        self.window_name = "AutoSkinnerUI"
        self.window_title = "Adam's Auto Skinner v1.0"

        if cmds.window(self.window_name, exists=True):
            cmds.deleteUI(self.window_name)

        # Defines the window
        self.auto_skin_window = cmds.window(
            self.window_name,
            title=self.window_title,
            width=280,
            height=180,
            sizeable=False,
            minimizeButton=False,
            maximizeButton=False,
        )
        self.main_layout = cmds.columnLayout(adjustableColumn=True)

        # Proxy geo section ---------------------------------------------------------------
        cmds.frameLayout("Create Proxy Geometry")
        self.secondary_layout = cmds.rowColumnLayout(
            numberOfColumns=3, columnWidth=[(1, 142), (2, 150), (3, 60)]
        )

        # Base mesh text field - requires an object name
        cmds.text(label="Base mesh:  ", align="right")
        self.base_mesh_txt_field = cmds.textField(
            "BaseMeshTextField", annotation="Enter base mesh name."
        )
        cmds.button(
            label="Add",
            command=lambda *args: self.add_selected(self.base_mesh_txt_field),
        )

        # Root joint text field - requires the name of the root joint of the skeleton
        cmds.text(label="Skeleton:  ", align="right")
        self.skeleton_txt_field = cmds.textField(
            "SkeletonTextField", annotation="Enter the root joint of your skeleton."
        )
        cmds.button(
            label="Add",
            command=lambda *args: self.add_selected(self.skeleton_txt_field),
        )

        cmds.setParent(self.main_layout)
        cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 65), (2, 200)])
        cmds.separator(style="none")
        self.prefix_option_menu = cmds.optionMenu(
            "PrefixOptionMenu",
            label="Joint Naming:",
            annotation="Are the joints sides named with a prefix or suffix?",
        )
        [cmds.menuItem("{name}", label=name) for name in ["Suffix", "Prefix"]]

        cmds.setParent(self.main_layout)
        self.individual_geo_size = cmds.floatFieldGrp(
            "IndividualGeoSizeMultiplier",
            label="Geo scale:  ",
            numberOfFields=3,
            value=[10.0 for value in range(1, 5)],
            annotation="Specifies individual scales for each axis in cm.",
        )

        cmds.setParent(self.main_layout)
        cmds.separator(height=10)

        # Creates the proxy geometry based on the previous parameters
        self.proxy_skin_geo_button = cmds.button(
            "ProxySkinGeoButton",
            label="Generate Proxy Skin",
            command=self.create_proxy_skin_geometry,
            backgroundColor=[0.5 for value in range(1, 4)],
            annotation="Generate proxy skin geo.",
        )
        cmds.separator(height=10)

        # Load Proxy Geo section ---------------------------------------------------------------
        cmds.rowColumnLayout(
            numberOfColumns=6,
            columnWidth=[(1, 30), (2, 97), (3, 15), (4, 150), (5, 60)],
        )

        cmds.separator(style="none")
        cmds.text(label="Load proxy geo:  ", align="right")
        self.proxy_geo_check_box = cmds.checkBox(
            onCommand=self.load_geo_check, offCommand=self.load_geo_check
        )
        self.load_proxy_geo_txt_field = cmds.textField(
            annotation="Enter existing proxy geo group name.", enable=False
        )
        self.add_proxy_geo_button = cmds.button(
            label="Add",
            enable=False,
            command=lambda *args: self.add_selected(self.load_proxy_geo_txt_field),
        )

        # Mirror Proxy Geo section ---------------------------------------------------------------
        cmds.setParent(self.main_layout)
        cmds.separator(height=10)
        cmds.button(
            "MirrorGeoButton",
            label="Mirror",
            command=self.mirror_proxy_geo,
            backgroundColor=[0.5 for value in range(1, 4)],
            annotation="Mirror proxy geometry positive to negative across the YZ plane.",
        )
        cmds.separator(height=10)

        # Bind Skin section ---------------------------------------------------------------
        cmds.frameLayout("Skin Weights")
        cmds.setParent(self.main_layout)
        cmds.separator(height=10)

        self.max_influences_field = cmds.intSliderGrp(
            "MaxInfluences",
            label="Max influences:   ",
            value=3,
            field=True,
            minValue=1,
            maxValue=30,
        )
        cmds.separator(height=10)
        self.smoothing_iterations = cmds.intSliderGrp(
            "SmoothIterations",
            label="Smoothing Iterations:   ",
            value=10,
            field=True,
            minValue=0,
            maxValue=200,
        )
        self.smoothing_step = cmds.floatSliderGrp(
            "SmoothingStep",
            label="Smoothing Step:   ",
            value=0.5,
            field=True,
            minValue=0,
            maxValue=1,
        )
        cmds.separator(height=10)
        cmds.button(
            "Bind",
            label="Bind",
            backgroundColor=[0.5 for value in range(1, 4)],
            command=self.bind,
            annotation="Bakes the deformation into linear skin weights.",
        )
        cmds.separator(height=5)
        # Show UI
        cmds.showWindow()

    def load_geo_check(self, *args):
        """
        Enables and disables parts of the UI depending on if the user wants to load proxy geo or create it.
        :param *args: Receives an extra argument from the cmds.button() function
        :return: None
        """
        self.proxy_geo_check = cmds.checkBox(
            self.proxy_geo_check_box, query=True, value=True
        )
        cmds.button(
            self.proxy_skin_geo_button, edit=True, enable=not self.proxy_geo_check
        )
        cmds.textField(
            self.load_proxy_geo_txt_field, edit=True, enable=self.proxy_geo_check
        )
        cmds.button(self.add_proxy_geo_button, edit=True, enable=self.proxy_geo_check)

    def create_proxy_skin_geometry(self, *args):
        """
        Creates the proxy geometry that is used to define the weight values in the bind_proxy_skin() function.
        :param *args: Receives an extra argument from the cmds.button() function
        :return: None
        """

        if cmds.objExists("proxy_skin_geo_grp"):
            cmds.error(
                "Proxy Skin already created. Delete the existing group to start again."
            )

        self.bind_joints = self.get_joints()

        self.proxy_skin_geo_grp = cmds.group(empty=True, name="proxy_skin_geo_grp")
        self.hide_proxy_skin_geo_grp = cmds.setAttr(
            f"{self.proxy_skin_geo_grp}.hiddenInOutliner", 1
        )
        self.geo_size_result = cmds.floatFieldGrp(
            self.individual_geo_size, query=True, value=True
        )

        self.scene_unit = cmds.currentUnit(query=True, linear=True)
        if self.scene_unit != "cm":
            cmds.currentUnit(linear="cm")

        for joint in self.bind_joints[0]:
            cube = cmds.polyCube(
                name=f"{joint}_proxy_skin_geo",
                width=self.geo_size_result[0],
                height=self.geo_size_result[1],
                depth=self.geo_size_result[2],
                constructionHistory=False,
            )

            joint_position = cmds.xform(joint, query=True, matrix=True, worldSpace=True)
            place_cube = cmds.xform(cube, matrix=joint_position, worldSpace=True)
            parent_cube = cmds.parent(cube, self.proxy_skin_geo_grp)

        self.set_unit_back = cmds.currentUnit(linear=self.scene_unit)
        self.proxy_geometry = cmds.listRelatives(self.proxy_skin_geo_grp, children=True)
        self.template_base_mesh = [
            cmds.setAttr(f"{self.bind_joints[2]}{attr}", 1)
            for attr in [".overrideEnabled", ".overrideDisplayType"]
        ]

    def bind(self, *args):
        """
        Binds the proxy geometry to the skeleton of the root joint specified and then copies those weights over to the base mesh.
        :param *args: Receives an extra argument from the cmds.button() function
        :return: None
        """
        self.bind_joints = self.get_joints()

        for geo in self.proxy_geometry:
            skin_cluster = cmds.skinCluster(
                self.bind_joints[0],
                geo,
                toSelectedBones=True,
                bindMethod=0,
                normalizeWeights=1,
            )[0]
            flood_weights = cmds.skinPercent(
                skin_cluster,
                geo,
                transformValue=[(geo.replace("_proxy_skin_geo", ""), 1.0)],
            )
            unlock_attributes = [
                cmds.setAttr(f"{geo}.{vector}{axis}", lock=False)
                for axis in ["X", "Y", "Z"]
                for vector in ["translate", "rotate", "scale"]
            ]
            freeze_attributes = cmds.makeIdentity(
                geo, apply=True, translate=True, rotate=True, scale=True
            )

        self.full_proxy_geo = cmds.polyUniteSkinned(
            self.proxy_geometry, constructionHistory=True
        )[0]
        self.hide_full_proxy_geo = cmds.setAttr(
            f"{self.full_proxy_geo}.hiddenInOutliner", 1
        )
        self.proxy_geo_history = cmds.listHistory(self.full_proxy_geo)
        self.source_skin_cluster = [
            node
            for node in self.proxy_geo_history
            if cmds.nodeType(node) == "skinCluster"
        ]

        self.base_geo_skin_cluster = cmds.skinCluster(
            self.bind_joints[0],
            self.bind_joints[2],
            toSelectedBones=True,
            bindMethod=0,
            normalizeWeights=1,
        )
        self.copy_weights_to_base_geo = cmds.copySkinWeights(
            sourceSkin=self.source_skin_cluster[0],
            destinationSkin=self.base_geo_skin_cluster[0],
            noMirror=True,
            surfaceAssociation="closestPoint",
        )

        self.template_proxy_geo = [
            cmds.setAttr(f"{self.full_proxy_geo}{attr}", 1)
            for attr in [".overrideEnabled", ".overrideDisplayType"]
        ]
        self.untemplate_base_mesh = cmds.setAttr(
            f"{self.bind_joints[2]}.overrideDisplayType", 0
        )

        self.smoothing_iterations_result = cmds.intSliderGrp(
            self.smoothing_iterations, query=True, value=True
        )
        self.smoothing_step_result = cmds.floatSliderGrp(
            self.smoothing_step, query=True, value=True
        )
        self.delta_mush = cmds.deltaMush(
            self.bind_joints[2],
            smoothingIterations=self.smoothing_iterations_result,
            smoothingStep=self.smoothing_step_result,
        )

        delete_proxy_geo = cmds.delete(self.full_proxy_geo, self.proxy_skin_geo_grp)
        self.max_influences_result = cmds.intSliderGrp(
            self.max_influences_field, query=True, value=True
        )

        cmds.bakeDeformer(
            srcSkeletonName=self.bind_joints[1],
            srcMeshName=self.bind_joints[2],
            dstSkeletonName=self.bind_joints[1],
            dstMeshName=self.bind_joints[2],
            maxInfluences=self.max_influences_result,
        )

    def add_selected(self, name):
        """
        Display first selected object to specified text field.
        :param name: Text field variable name
        :return: None
        """
        selection = cmds.ls(selection=True)
        if selection:
            cmds.textField(name, edit=True, text=selection[0])

    def get_joints(self):
        """
        Checks the base mesh and skeleton fields from the UI to see if they are valid and the objects exist.
        :param *args: Receives an extra argument from the cmds.button() function
        :return: list - bind joints
        :return: string - root joint
        :return: string - base mesh
        """
        self.base_mesh_result = cmds.textField(
            self.base_mesh_txt_field, query=True, text=True
        )
        self.skeleton_result = cmds.textField(
            self.skeleton_txt_field, query=True, text=True
        )

        if not cmds.objExists(self.base_mesh_result):
            cmds.error(
                f"Please provide a valid poly mesh for Base mesh field.",
                noContext=True,
                showLineNumber=False,
            )
        self.base_mesh_history = cmds.listHistory(self.base_mesh_result)
        for history in self.base_mesh_history:
            if cmds.nodeType(history) == "skinCluster":
                cmds.error(
                    f"'{self.base_mesh_result}' is already connected to a skin cluster.",
                    noContext=True,
                    showLineNumber=False,
                )

        if (
            not cmds.objExists(self.skeleton_result)
            or cmds.nodeType(self.skeleton_result) != "joint"
        ):
            cmds.error(
                "Please provide a valid joint for Skeleton field.",
                noContext=True,
                showLineNumber=False,
            )

        self.joint_children = cmds.listRelatives(
            self.skeleton_result, type="joint", allDescendents=True
        )
        if not self.joint_children:
            cmds.error(
                f"{self.skeleton_result} is not a root joint.",
                noContext=True,
                showLineNumber=False,
            )
        self.joint_children.append(self.skeleton_result)
        self.joint_heirarchy = [
            joint_name for joint_name in self.joint_children if "bind" in joint_name
        ]

        return self.joint_heirarchy, self.skeleton_result, self.base_mesh_result

    def mirror_proxy_geo(self, *args):
        """
        Mirrors the self.proxy_geometry from left(+) to right(-) in X / YZ plane
        :param *args: Receives an extra argument from the cmds.button() function
        :return: None
        """
        if not cmds.objExists("proxy_skin_geo_grp"):
            cmds.error(
                "No proxy geometry created. Unable to mirror.",
                noContext=True,
                showLineNumber=False,
            )

        self.joint_prefix = cmds.optionMenu(
            self.prefix_option_menu, query=True, value=True
        )
        self.prefixes = {"l": "r", "lf": "rt", "left": "right"}

        self.proxy_geo_check = cmds.checkBox(
            self.proxy_geo_check_box, query=True, value=True
        )

        if self.proxy_geo_check == True:
            self.proxy_geo_field_result = cmds.textField(
                self.load_proxy_geo_txt_field, query=True, text=True
            )
            if (
                not cmds.objExists(self.proxy_geo_field_result)
                or cmds.nodeType(self.proxy_geo_field_result) != "transform"
            ):
                cmds.error(
                    "Please select a valid transform/group which contains the proxy geometry",
                    noContext=True,
                    showLineNumber=False,
                )

            self.proxy_geometry = cmds.listRelatives(
                self.proxy_geo_field_result, children=True, type="transform"
            )
            self.proxy_skin_geo_grp = self.proxy_geo_field_result

        for object in self.proxy_geometry:
            if self.joint_prefix == "Prefix":
                self.object_prefix = None
                for key, value in self.prefixes.items():
                    if object.startswith(key):
                        self.object_prefix = key
                        self.opposite_object_prefix = value
                        break

            if self.joint_prefix == "Suffix":
                self.object_prefix = None
                for key, value in self.prefixes.items():
                    if object.split("_")[-4] == key:
                        self.object_prefix = key
                        self.opposite_object_prefix = value
                        break

            if self.object_prefix is not None:
                new_object = cmds.duplicate(object)[0]

                if self.joint_prefix == "Prefix":
                    self.match_name = f"{self.opposite_object_prefix}{new_object.removeprefix(self.object_prefix)[:-1]}"
                if self.joint_prefix == "Suffix":
                    self.match_name = f"{new_object[:-16].removesuffix(self.object_prefix)}{self.opposite_object_prefix}_proxy_skin_geo"

                delete_opposite_object = cmds.delete(self.match_name)
                renamed_object = cmds.rename(new_object, self.match_name)
                transform = cmds.group(empty=True)
                parent_object = cmds.parent(renamed_object, transform)

                inverse_transform = cmds.setAttr(f"{transform}.scaleX", -1)
                freeze_transform = cmds.makeIdentity(transform, apply=True, scale=True)
                unparent_object = cmds.parent(renamed_object, world=True)

                reverse_object_normals = cmds.polyNormal(renamed_object)
                delete_object_history = cmds.DeleteHistory(renamed_object)
                delete_transform = cmds.delete(transform)

                cmds.parent(renamed_object, self.proxy_skin_geo_grp)
                clear_selection = cmds.select(clear=True)
            else:
                continue


if __name__ == "__main__":
    run_auto_skinner = AutoSkinner()