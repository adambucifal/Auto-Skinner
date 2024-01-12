auto_skinner is a python script for maya that helps the blocking out process for skinning.

It builds a proxy geometry which the user uses to model the rough shapes/volumes of where each joint should have influence. 
Then it takes that information and turns it into skin weights, applies a smooth algorithm (delta mush) and bakes everything back down into linear skin weights.
