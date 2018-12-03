# CODE

NARM.py -- Main code -- Run this to train models - Needs Theano

# DATA

All of the data preprocessing code is agnostic to Theano except https://github.com/prashant-jayan21/sessionRec_NARM/blob/master/data_process.py#L32. You may want to edit it as per your needs when you switch to using TensorFlow.

The datasets which will be used currently by NARM.py are:
- data/train_dummy.pkl
- data/test_dummy.pkl

(The validation set is created on-the-fly in the code.)

These are dummy datasets in the right format but don't include all of the data. These should be used for development purposes as using the full datasets will slow you down too much. (Prashant will provide the full datasets soon...)

# CODING GUIDELINES

Please do not push to master if your changes are unstable. Always work on a separate branch and merge to master whenever ready.




