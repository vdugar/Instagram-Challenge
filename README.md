An attempt to solve the [Instagram Challenge](http://instagram-engineering.tumblr.com/post/12651721845/instagram-engineering-challenge-the-unshredder).

Given an image that has been shredded into 'n' equal-width jumbled  columns, this script attempts to put the image back together (or 'unshred' it).

### Usage:

`python shredder.py [source_image] [NO_OF_SHREDS]`
*Use this to shred the image*

`python instagram.py [shredded_image] [NO_OF_SHREDS] [shred_method]`
*The unshredder. Outputs to 'unshredded.jpg'*
*shred_method can be either one of the following-*
*edge : Uses edge detection*
*euc : Uses Euclidean distances over average pixels*

*Note-> Both the shredder and unshredder work properly only if (IMAGE_WIDTH / NO_OF_SHREDS) is a whole number.*
