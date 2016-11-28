.. _ref-brain:

Code documentation
==================

Learner Factory
----------------
Learners are created with factory classes.  The `JointProbLearnerFactory` class is responsible for properly
configuring and initializing joint probability learners.  Use this class to specify the name, features, and levels
of new learners.

Example:

.. code-block:: python

    from brain import JointProbLearnerFactory

    # create a learner
    factory = JointProbLearnerFactory('medical')
    factory.add_feature('gender', kind='str_categorical',  levels_or_edges=['male', 'female'])
    factory.add_feature('age', kind='continuous', levels_or_edges=[0, 20, 30, 40, 50, 60])
    factory.add_feature('diabetic', kind='int_categorical',  levels_or_edges=[0, 1])
    factory.create()

.. autoclass:: brain.factories.JointProbLearnerFactory
    :members:

Learner
-----------------
The `JointProbLearner` class is the main interface for django-brain.  It is used to both train learners and extract
information from them.

Example:

.. code-block:: python

    from brain import JointProbLearnerFactory, JointProbLearner

    # create a learner
    factory = JointProbLearnerFactory('medical')
    factory.add_feature('gender', kind='str_categorical',  levels_or_edges=['male', 'female'])
    factory.add_feature('age', kind='continuous', levels_or_edges=[0, 20, 30, 40, 50, 60])
    factory.add_feature('diabetic', kind='int_categorical',  levels_or_edges=[0, 1])
    factory.create()

    # train a learner
    lrn = JointProbLearner('medical')
    lrn.add_observations([
        {'gender': 'male', 'age': 37, 'diabetic': 1},
        {'gender': 'female', 'age': 57, 'diabetic': 0},
        .
        .
        {'gender': 'male', 'age': 17, 'diabetic': 1},
    ])

    # get a Dataframe of all probabilities
    df_probs = lrn.probs

    # get probability of encountering specific scenarios
    prob_list = lrn.probabilities_for_observations([
        {'gender': 'female', 'age': 24, 'diabetic': 0},
        {'gender': 'male', 'age': 68, 'diabetic': 1},
        .
        .
    ])

.. autoclass:: brain.joint_prob_learner.JointProbLearner
    :members:



Feature
-----------------
Any given learner has a collection of `Feature` class instances that is uses to manage it's features.  This class is
not intended to be directly instantiated by the user, but it does expose several methods that end users will find
quite useful.

.. autoclass:: brain.joint_prob_learner.Feature
    :members:

Joint Normal Distributions
--------------------------
An instance of the `JointNormal` class is maintained for each grid point of a JointProbLearner that has defined normal
variables.  This class provides an interface for training and extracting information from joint-normal distributions.
There is quite a bit of math going on behind the scenes in this class.  A terse writeup providing the necessary
background for understanding it can be obtained from https://github.com/robdmc/stats_for_software .

Example:

.. code-block:: python

    from brain import JointNormal

    # Create a standard normal distribution assuming it was generated from 10 observations.
    # Set up to forget old observations using an n_max of 100 observations. 
    N = JointNormal(labels=['x', 'y'], mu=[0, 0], cov=[[1, 0], [0, 1]], N=10, n_max=100)

    # Add observations to the distribution
    N.ingest([
        {'x': 1.0, 'y': 3.0},
        {'x': -0.6, 'y': 1.2},
        {'x': -2.0, 'y': -4.3},
    ])

    # find marginal estimates for parameters
    x_mu, x_std = N.estimate('x')
    y_mu, y_std = N.estimate('y')

    # find conditional estimates for parameters
    x_mu, x_std = N.estimate('x', y=1)
    y_mu, y_std = N.estimate('y', x=1)

    # get log probability density at a point
    dens = N.log_density(dict(x=2, y=-1))

    # find probabilities that a variable exceeds some limit
    p_marginal = N.probability(x__gt=2)

    # find probabilities that y is less than threshold given a value for x
    p_conditional = N.probability(y__lt=2, x=1)

    # multiply two independent joint normal distributions together and look at params
    N1 = JointNormal(labels=['x', 'y'], mu=[0, 0], cov=[[1, 0], [0, 1]])
    N2 = JointNormal(labels=['x', 'y'], mu=[1, 1], cov=[[2, 0], [0, 2]])
    N3 = N1 * N2
    mu_x_3, sig_x_3 = N3.estimate('x')

    # create a 3-d distribution to demonstrate marginalization and conditioning
    N4 = JointNormal(
        labels=['x', 'y', 'z'],
        mu=[0, 0, 0],
        cov=[[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    )
    # marginalize out the z variable
    N_marg = N4.marginalize('x', 'y')
    N_marg.labels  # will be equal to ['x', 'y']

    # condition on x and y variables
    N_cond = N4.conditional(x=1, y=1)
    N_cond.labels  # will be equal to ['z']




.. automodule:: brain.joint_normal
    :members:

