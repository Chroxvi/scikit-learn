"""
Testing for the tree module (sklearn.tree).
"""
import copy
import pickle
from itertools import product
import struct

import pytest
import numpy as np
from numpy.testing import assert_allclose
from scipy.sparse import csc_matrix
from scipy.sparse import csr_matrix
from scipy.sparse import coo_matrix

from sklearn.random_projection import _sparse_random_matrix

from sklearn.dummy import DummyRegressor

from sklearn.metrics import accuracy_score
from sklearn.metrics import mean_squared_error
from sklearn.metrics import mean_poisson_deviance

from sklearn.model_selection import train_test_split

from sklearn.utils._testing import assert_array_equal
from sklearn.utils._testing import assert_array_almost_equal
from sklearn.utils._testing import assert_almost_equal
from sklearn.utils._testing import assert_warns
from sklearn.utils._testing import assert_warns_message
from sklearn.utils._testing import create_memmap_backed_data
from sklearn.utils._testing import ignore_warnings
from sklearn.utils._testing import skip_if_32bit

from sklearn.utils.estimator_checks import check_sample_weights_invariance
from sklearn.utils.validation import check_random_state

from sklearn.exceptions import NotFittedError

from sklearn.tree import DecisionTreeClassifier
from sklearn.tree import DecisionTreeRegressor
from sklearn.tree import ExtraTreeClassifier
from sklearn.tree import ExtraTreeRegressor

from sklearn import tree
from sklearn.tree._tree import TREE_LEAF, TREE_UNDEFINED
from sklearn.tree._classes import CRITERIA_CLF
from sklearn.tree._classes import CRITERIA_REG
from sklearn import datasets

from sklearn.utils import compute_sample_weight

CLF_CRITERIONS = ("gini", "entropy")
REG_CRITERIONS = ("mse", "mae", "friedman_mse", "poisson")

CLF_TREES = {
    "DecisionTreeClassifier": DecisionTreeClassifier,
    "ExtraTreeClassifier": ExtraTreeClassifier,
}

REG_TREES = {
    "DecisionTreeRegressor": DecisionTreeRegressor,
    "ExtraTreeRegressor": ExtraTreeRegressor,
}

ALL_TREES = dict()
ALL_TREES.update(CLF_TREES)
ALL_TREES.update(REG_TREES)

SPARSE_TREES = ["DecisionTreeClassifier", "DecisionTreeRegressor",
                "ExtraTreeClassifier", "ExtraTreeRegressor"]

REG_TREE_VALUE_DTYPES = [None, np.float64, np.float32, np.float16]
CLF_TREE_VALUE_DTYPES = REG_TREE_VALUE_DTYPES + [
    np.uint64, np.uint32, np.uint16, np.uint8]

X_small = np.array([
    [0, 0, 4, 0, 0, 0, 1, -14, 0, -4, 0, 0, 0, 0, ],
    [0, 0, 5, 3, 0, -4, 0, 0, 1, -5, 0.2, 0, 4, 1, ],
    [-1, -1, 0, 0, -4.5, 0, 0, 2.1, 1, 0, 0, -4.5, 0, 1, ],
    [-1, -1, 0, -1.2, 0, 0, 0, 0, 0, 0, 0.2, 0, 0, 1, ],
    [-1, -1, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 1, ],
    [-1, -2, 0, 4, -3, 10, 4, 0, -3.2, 0, 4, 3, -4, 1, ],
    [2.11, 0, -6, -0.5, 0, 11, 0, 0, -3.2, 6, 0.5, 0, -3, 1, ],
    [2.11, 0, -6, -0.5, 0, 11, 0, 0, -3.2, 6, 0, 0, -2, 1, ],
    [2.11, 8, -6, -0.5, 0, 11, 0, 0, -3.2, 6, 0, 0, -2, 1, ],
    [2.11, 8, -6, -0.5, 0, 11, 0, 0, -3.2, 6, 0.5, 0, -1, 0, ],
    [2, 8, 5, 1, 0.5, -4, 10, 0, 1, -5, 3, 0, 2, 0, ],
    [2, 0, 1, 1, 1, -1, 1, 0, 0, -2, 3, 0, 1, 0, ],
    [2, 0, 1, 2, 3, -1, 10, 2, 0, -1, 1, 2, 2, 0, ],
    [1, 1, 0, 2, 2, -1, 1, 2, 0, -5, 1, 2, 3, 0, ],
    [3, 1, 0, 3, 0, -4, 10, 0, 1, -5, 3, 0, 3, 1, ],
    [2.11, 8, -6, -0.5, 0, 1, 0, 0, -3.2, 6, 0.5, 0, -3, 1, ],
    [2.11, 8, -6, -0.5, 0, 1, 0, 0, -3.2, 6, 1.5, 1, -1, -1, ],
    [2.11, 8, -6, -0.5, 0, 10, 0, 0, -3.2, 6, 0.5, 0, -1, -1, ],
    [2, 0, 5, 1, 0.5, -2, 10, 0, 1, -5, 3, 1, 0, -1, ],
    [2, 0, 1, 1, 1, -2, 1, 0, 0, -2, 0, 0, 0, 1, ],
    [2, 1, 1, 1, 2, -1, 10, 2, 0, -1, 0, 2, 1, 1, ],
    [1, 1, 0, 0, 1, -3, 1, 2, 0, -5, 1, 2, 1, 1, ],
    [3, 1, 0, 1, 0, -4, 1, 0, 1, -2, 0, 0, 1, 0, ]])

y_small = [1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0,
           0, 0]
y_small_reg = [1.0, 2.1, 1.2, 0.05, 10, 2.4, 3.1, 1.01, 0.01, 2.98, 3.1, 1.1,
               0.0, 1.2, 2, 11, 0, 0, 4.5, 0.201, 1.06, 0.9, 0]

# toy sample
X = [[-2, -1], [-1, -1], [-1, -2], [1, 1], [1, 2], [2, 1]]
y = [-1, -1, -1, 1, 1, 1]
T = [[-1, -1], [2, 2], [3, 2]]
true_result = [-1, 1, 1]

# also load the iris dataset
# and randomly permute it
iris = datasets.load_iris()
rng = np.random.RandomState(1)
perm = rng.permutation(iris.target.size)
iris.data = iris.data[perm]
iris.target = iris.target[perm]

# also load the diabetes dataset
# and randomly permute it
diabetes = datasets.load_diabetes()
perm = rng.permutation(diabetes.target.size)
diabetes.data = diabetes.data[perm]
diabetes.target = diabetes.target[perm]

digits = datasets.load_digits()
perm = rng.permutation(digits.target.size)
digits.data = digits.data[perm]
digits.target = digits.target[perm]

random_state = check_random_state(0)
X_multilabel, y_multilabel = datasets.make_multilabel_classification(
    random_state=0, n_samples=30, n_features=10)

# NB: despite their names X_sparse_* are numpy arrays (and not sparse matrices)
X_sparse_pos = random_state.uniform(size=(20, 5))
X_sparse_pos[X_sparse_pos <= 0.8] = 0.
y_random = random_state.randint(0, 4, size=(20, ))
X_sparse_mix = _sparse_random_matrix(20, 10, density=0.25,
                                     random_state=0).toarray()


DATASETS = {
    "iris": {"X": iris.data, "y": iris.target},
    "diabetes": {"X": diabetes.data, "y": diabetes.target},
    "digits": {"X": digits.data, "y": digits.target},
    "toy": {"X": X, "y": y},
    "clf_small": {"X": X_small, "y": y_small},
    "reg_small": {"X": X_small, "y": y_small_reg},
    "multilabel": {"X": X_multilabel, "y": y_multilabel},
    "sparse-pos": {"X": X_sparse_pos, "y": y_random},
    "sparse-neg": {"X": - X_sparse_pos, "y": y_random},
    "sparse-mix": {"X": X_sparse_mix, "y": y_random},
    "zeros": {"X": np.zeros((20, 3)), "y": y_random}
}

for name in DATASETS:
    DATASETS[name]["X_sparse"] = csc_matrix(DATASETS[name]["X"])


def assert_tree_equal(d, s, message):
    assert s.node_count == d.node_count, (
        "{0}: inequal number of node ({1} != {2})"
        "".format(message, s.node_count, d.node_count))

    assert_array_equal(d.children_right, s.children_right,
                       message + ": inequal children_right")
    assert_array_equal(d.children_left, s.children_left,
                       message + ": inequal children_left")

    external = d.children_right == TREE_LEAF
    internal = np.logical_not(external)

    assert_array_equal(d.feature[internal], s.feature[internal],
                       message + ": inequal features")
    assert_array_equal(d.threshold[internal], s.threshold[internal],
                       message + ": inequal threshold")
    assert_array_equal(d.n_node_samples.sum(), s.n_node_samples.sum(),
                       message + ": inequal sum(n_node_samples)")
    assert_array_equal(d.n_node_samples, s.n_node_samples,
                       message + ": inequal n_node_samples")

    assert_almost_equal(d.impurity, s.impurity,
                        err_msg=message + ": inequal impurity")

    assert_array_almost_equal(d.value[external], s.value[external],
                              err_msg=message + ": inequal value")


@pytest.mark.parametrize('tree_value_dtype', CLF_TREE_VALUE_DTYPES)
def test_classification_toy(tree_value_dtype):
    # Check classification on a toy dataset.
    for name, Tree in CLF_TREES.items():
        clf = Tree(random_state=0, store_tree_astype=tree_value_dtype)
        clf.fit(X, y)
        assert_array_equal(clf.predict(T), true_result,
                           "Failed with {0}".format(name))

        clf = Tree(max_features=1, random_state=1)
        clf.fit(X, y)
        assert_array_equal(clf.predict(T), true_result,
                           "Failed with {0}".format(name))


def test_weighted_classification_toy():
    # Check classification on a weighted toy dataset.
    for name, Tree in CLF_TREES.items():
        clf = Tree(random_state=0)

        clf.fit(X, y, sample_weight=np.ones(len(X)))
        assert_array_equal(clf.predict(T), true_result,
                           "Failed with {0}".format(name))

        clf.fit(X, y, sample_weight=np.full(len(X), 0.5))
        assert_array_equal(clf.predict(T), true_result,
                           "Failed with {0}".format(name))


@pytest.mark.parametrize("Tree", REG_TREES.values())
@pytest.mark.parametrize("criterion", REG_CRITERIONS)
@pytest.mark.parametrize('tree_value_dtype', REG_TREE_VALUE_DTYPES)
def test_regression_toy(Tree, criterion, tree_value_dtype):
    # Check regression on a toy dataset.
    if criterion == "poisson":
        # make target positive while not touching the original y and
        # true_result
        a = np.abs(np.min(y)) + 1
        y_train = np.array(y) + a
        y_test = np.array(true_result) + a
    else:
        y_train = y
        y_test = true_result

    reg = Tree(criterion=criterion, random_state=1,
               store_tree_astype=tree_value_dtype)
    reg.fit(X, y_train)
    assert_allclose(reg.predict(T), y_test)
    assert reg.predict(T).dtype == np.float64

    reg = Tree(criterion=criterion, max_features=1, random_state=1,
               store_tree_astype=tree_value_dtype)
    reg.fit(X, y_train)
    assert_allclose(reg.predict(T), y_test)
    assert reg.predict(T).dtype == np.float64


def test_xor():
    # Check on a XOR problem
    y = np.zeros((10, 10))
    y[:5, :5] = 1
    y[5:, 5:] = 1

    gridx, gridy = np.indices(y.shape)

    X = np.vstack([gridx.ravel(), gridy.ravel()]).T
    y = y.ravel()

    for name, Tree in CLF_TREES.items():
        clf = Tree(random_state=0)
        clf.fit(X, y)
        assert clf.score(X, y) == 1.0, "Failed with {0}".format(name)

        clf = Tree(random_state=0, max_features=1)
        clf.fit(X, y)
        assert clf.score(X, y) == 1.0, "Failed with {0}".format(name)


def test_iris():
    # Check consistency on dataset iris.
    for (name, Tree), criterion in product(CLF_TREES.items(), CLF_CRITERIONS):
        clf = Tree(criterion=criterion, random_state=0)
        clf.fit(iris.data, iris.target)
        score = accuracy_score(clf.predict(iris.data), iris.target)
        assert score > 0.9, (
            "Failed with {0}, criterion = {1} and score = {2}"
            "".format(name, criterion, score))

        clf = Tree(criterion=criterion, max_features=2, random_state=0)
        clf.fit(iris.data, iris.target)
        score = accuracy_score(clf.predict(iris.data), iris.target)
        assert score > 0.5, (
            "Failed with {0}, criterion = {1} and score = {2}"
            "".format(name, criterion, score))


@pytest.mark.parametrize("name, Tree", REG_TREES.items())
@pytest.mark.parametrize("criterion", REG_CRITERIONS)
@pytest.mark.parametrize('tree_value_dtype', REG_TREE_VALUE_DTYPES)
def test_diabetes_overfit(name, Tree, criterion, tree_value_dtype):
    # check consistency of overfitted trees on the diabetes dataset
    # since the trees will overfit, we expect an MSE of 0
    reg = Tree(criterion=criterion, random_state=0,
               store_tree_astype=tree_value_dtype)
    reg.fit(diabetes.data, diabetes.target)
    score = mean_squared_error(diabetes.target, reg.predict(diabetes.data))
    assert score == pytest.approx(0), (
        f"Failed with {name}, criterion = {criterion} and score = {score}"
    )


@skip_if_32bit
@pytest.mark.parametrize("name, Tree", REG_TREES.items())
@pytest.mark.parametrize(
    "criterion, max_depth, metric, max_loss",
    [("mse", 15, mean_squared_error, 60),
     ("mae", 20, mean_squared_error, 60),
     ("friedman_mse", 15, mean_squared_error, 60),
     ("poisson", 15, mean_poisson_deviance, 30)]
)
@pytest.mark.parametrize('tree_value_dtype', REG_TREE_VALUE_DTYPES)
def test_diabetes_underfit(
    name, Tree, criterion, max_depth, metric, max_loss, tree_value_dtype):
    # check consistency of trees when the depth and the number of features are
    # limited

    reg = Tree(
        criterion=criterion, max_depth=max_depth,
        max_features=6, random_state=0, store_tree_astype=tree_value_dtype
    )
    reg.fit(diabetes.data, diabetes.target)
    loss = metric(diabetes.target, reg.predict(diabetes.data))
    assert 0 < loss < max_loss


@pytest.mark.parametrize('tree_value_dtype', CLF_TREE_VALUE_DTYPES)
def test_probability(tree_value_dtype):
    # Predict probabilities using DecisionTreeClassifier.

    for name, Tree in CLF_TREES.items():
        clf = Tree(max_depth=1, max_features=1, random_state=42,
                   store_tree_astype=tree_value_dtype)
        clf.fit(iris.data, iris.target)

        prob_predict = clf.predict_proba(iris.data)
        assert_array_almost_equal(np.sum(prob_predict, 1),
                                  np.ones(iris.data.shape[0]),
                                  err_msg="Failed with {0}".format(name))
        assert_array_equal(np.argmax(prob_predict, 1),
                           clf.predict(iris.data),
                           err_msg="Failed with {0}".format(name))
        assert_almost_equal(clf.predict_proba(iris.data),
                            np.exp(clf.predict_log_proba(iris.data)), 8,
                            err_msg="Failed with {0}".format(name))
        assert prob_predict.dtype == np.float64


def test_arrayrepr():
    # Check the array representation.
    # Check resize
    X = np.arange(10000)[:, np.newaxis]
    y = np.arange(10000)

    for name, Tree in REG_TREES.items():
        reg = Tree(max_depth=None, random_state=0)
        reg.fit(X, y)


def test_pure_set():
    # Check when y is pure.
    X = [[-2, -1], [-1, -1], [-1, -2], [1, 1], [1, 2], [2, 1]]
    y = [1, 1, 1, 1, 1, 1]

    for name, TreeClassifier in CLF_TREES.items():
        clf = TreeClassifier(random_state=0)
        clf.fit(X, y)
        assert_array_equal(clf.predict(X), y,
                           err_msg="Failed with {0}".format(name))

    for name, TreeRegressor in REG_TREES.items():
        reg = TreeRegressor(random_state=0)
        reg.fit(X, y)
        assert_almost_equal(reg.predict(X), y,
                            err_msg="Failed with {0}".format(name))


def test_numerical_stability():
    # Check numerical stability.
    X = np.array([
        [152.08097839, 140.40744019, 129.75102234, 159.90493774],
        [142.50700378, 135.81935120, 117.82884979, 162.75781250],
        [127.28772736, 140.40744019, 129.75102234, 159.90493774],
        [132.37025452, 143.71923828, 138.35694885, 157.84558105],
        [103.10237122, 143.71928406, 138.35696411, 157.84559631],
        [127.71276855, 143.71923828, 138.35694885, 157.84558105],
        [120.91514587, 140.40744019, 129.75102234, 159.90493774]])

    y = np.array(
        [1., 0.70209277, 0.53896582, 0., 0.90914464, 0.48026916, 0.49622521])

    with np.errstate(all="raise"):
        for name, Tree in REG_TREES.items():
            reg = Tree(random_state=0)
            reg.fit(X, y)
            reg.fit(X, -y)
            reg.fit(-X, y)
            reg.fit(-X, -y)


@pytest.mark.parametrize('tree_value_dtype', CLF_TREE_VALUE_DTYPES)
def test_importances(tree_value_dtype):
    # Check variable importances.
    X, y = datasets.make_classification(n_samples=5000,
                                        n_features=10,
                                        n_informative=3,
                                        n_redundant=0,
                                        n_repeated=0,
                                        shuffle=False,
                                        random_state=0)

    for name, Tree in CLF_TREES.items():
        clf = Tree(random_state=0, store_tree_astype=tree_value_dtype)

        clf.fit(X, y)
        importances = clf.feature_importances_
        n_important = np.sum(importances > 0.1)

        assert importances.shape[0] == 10, "Failed with {0}".format(name)
        assert n_important == 3, "Failed with {0}".format(name)

    # Check on iris that importances are the same for all builders
    clf = DecisionTreeClassifier(random_state=0,
                                 store_tree_astype=tree_value_dtype)
    clf.fit(iris.data, iris.target)
    clf2 = DecisionTreeClassifier(random_state=0,
                                  max_leaf_nodes=len(iris.data),
                                  store_tree_astype=tree_value_dtype)
    clf2.fit(iris.data, iris.target)

    assert_array_equal(clf.feature_importances_,
                       clf2.feature_importances_)


def test_importances_raises():
    # Check if variable importance before fit raises ValueError.
    clf = DecisionTreeClassifier()
    with pytest.raises(ValueError):
        getattr(clf, 'feature_importances_')


def test_importances_gini_equal_mse():
    # Check that gini is equivalent to mse for binary output variable

    X, y = datasets.make_classification(n_samples=2000,
                                        n_features=10,
                                        n_informative=3,
                                        n_redundant=0,
                                        n_repeated=0,
                                        shuffle=False,
                                        random_state=0)

    # The gini index and the mean square error (variance) might differ due
    # to numerical instability. Since those instabilities mainly occurs at
    # high tree depth, we restrict this maximal depth.
    clf = DecisionTreeClassifier(criterion="gini", max_depth=5,
                                 random_state=0).fit(X, y)
    reg = DecisionTreeRegressor(criterion="mse", max_depth=5,
                                random_state=0).fit(X, y)

    assert_almost_equal(clf.feature_importances_, reg.feature_importances_)
    assert_array_equal(clf.tree_.feature, reg.tree_.feature)
    assert_array_equal(clf.tree_.children_left, reg.tree_.children_left)
    assert_array_equal(clf.tree_.children_right, reg.tree_.children_right)
    assert_array_equal(clf.tree_.n_node_samples, reg.tree_.n_node_samples)


def test_max_features():
    # Check max_features.
    for name, TreeRegressor in REG_TREES.items():
        reg = TreeRegressor(max_features="auto")
        reg.fit(diabetes.data, diabetes.target)
        assert reg.max_features_ == diabetes.data.shape[1]

    for name, TreeClassifier in CLF_TREES.items():
        clf = TreeClassifier(max_features="auto")
        clf.fit(iris.data, iris.target)
        assert clf.max_features_ == 2

    for name, TreeEstimator in ALL_TREES.items():
        est = TreeEstimator(max_features="sqrt")
        est.fit(iris.data, iris.target)
        assert (est.max_features_ ==
                int(np.sqrt(iris.data.shape[1])))

        est = TreeEstimator(max_features="log2")
        est.fit(iris.data, iris.target)
        assert (est.max_features_ ==
                int(np.log2(iris.data.shape[1])))

        est = TreeEstimator(max_features=1)
        est.fit(iris.data, iris.target)
        assert est.max_features_ == 1

        est = TreeEstimator(max_features=3)
        est.fit(iris.data, iris.target)
        assert est.max_features_ == 3

        est = TreeEstimator(max_features=0.01)
        est.fit(iris.data, iris.target)
        assert est.max_features_ == 1

        est = TreeEstimator(max_features=0.5)
        est.fit(iris.data, iris.target)
        assert (est.max_features_ ==
                int(0.5 * iris.data.shape[1]))

        est = TreeEstimator(max_features=1.0)
        est.fit(iris.data, iris.target)
        assert est.max_features_ == iris.data.shape[1]

        est = TreeEstimator(max_features=None)
        est.fit(iris.data, iris.target)
        assert est.max_features_ == iris.data.shape[1]

        # use values of max_features that are invalid
        est = TreeEstimator(max_features=10)
        with pytest.raises(ValueError):
            est.fit(X, y)

        est = TreeEstimator(max_features=-1)
        with pytest.raises(ValueError):
            est.fit(X, y)

        est = TreeEstimator(max_features=0.0)
        with pytest.raises(ValueError):
            est.fit(X, y)

        est = TreeEstimator(max_features=1.5)
        with pytest.raises(ValueError):
            est.fit(X, y)

        est = TreeEstimator(max_features="foobar")
        with pytest.raises(ValueError):
            est.fit(X, y)


def test_error():
    # Test that it gives proper exception on deficient input.
    for name, TreeEstimator in CLF_TREES.items():
        # predict before fit
        est = TreeEstimator()
        with pytest.raises(NotFittedError):
            est.predict_proba(X)

        est.fit(X, y)
        X2 = [[-2, -1, 1]]  # wrong feature shape for sample
        with pytest.raises(ValueError):
            est.predict_proba(X2)

        # store_tree_astype must be float when not using postive int weights
        with pytest.raises(ValueError):
            TreeEstimator(store_tree_astype=np.uint32).fit(
                X, y, sample_weight=np.ones_like(y) + 0.1)
        with pytest.raises(ValueError):
            TreeEstimator(store_tree_astype=np.uint32).fit(
                X, y, sample_weight=np.ones_like(y) - 2)

    for name, TreeEstimator in ALL_TREES.items():
        with pytest.raises(ValueError):
            TreeEstimator(min_samples_leaf=-1).fit(X, y)
        with pytest.raises(ValueError):
            TreeEstimator(min_samples_leaf=.6).fit(X, y)
        with pytest.raises(ValueError):
            TreeEstimator(min_samples_leaf=0.).fit(X, y)
        with pytest.raises(ValueError):
            TreeEstimator(min_samples_leaf=3.).fit(X, y)
        with pytest.raises(ValueError):
            TreeEstimator(min_weight_fraction_leaf=-1).fit(X, y)
        with pytest.raises(ValueError):
            TreeEstimator(min_weight_fraction_leaf=0.51).fit(X, y)
        with pytest.raises(ValueError):
            TreeEstimator(min_samples_split=-1).fit(X, y)
        with pytest.raises(ValueError):
            TreeEstimator(min_samples_split=0.0).fit(X, y)
        with pytest.raises(ValueError):
            TreeEstimator(min_samples_split=1.1).fit(X, y)
        with pytest.raises(ValueError):
            TreeEstimator(min_samples_split=2.5).fit(X, y)
        with pytest.raises(ValueError):
            TreeEstimator(max_depth=-1).fit(X, y)
        with pytest.raises(ValueError):
            TreeEstimator(max_features=42).fit(X, y)
        # min_impurity_split warning
        with ignore_warnings(category=FutureWarning):
            with pytest.raises(ValueError):
                TreeEstimator(min_impurity_split=-1.0).fit(X, y)
        with pytest.raises(ValueError):
            TreeEstimator(min_impurity_decrease=-1.0).fit(X, y)

        # Wrong dimensions
        est = TreeEstimator()
        y2 = y[:-1]
        with pytest.raises(ValueError):
            est.fit(X, y2)

        # Test with arrays that are non-contiguous.
        Xf = np.asfortranarray(X)
        est = TreeEstimator()
        est.fit(Xf, y)
        assert_almost_equal(est.predict(T), true_result)

        # predict before fitting
        est = TreeEstimator()
        with pytest.raises(NotFittedError):
            est.predict(T)

        # predict on vector with different dims
        est.fit(X, y)
        t = np.asarray(T)
        with pytest.raises(ValueError):
            est.predict(t[:, 1:])

        # wrong sample shape
        Xt = np.array(X).T

        est = TreeEstimator()
        est.fit(np.dot(X, Xt), y)
        with pytest.raises(ValueError):
            est.predict(X)
        with pytest.raises(ValueError):
            est.apply(X)

        clf = TreeEstimator()
        clf.fit(X, y)
        with pytest.raises(ValueError):
            clf.predict(Xt)
        with pytest.raises(ValueError):
            clf.apply(Xt)

        # apply before fitting
        est = TreeEstimator()
        with pytest.raises(NotFittedError):
            est.apply(T)

        # invalid types for store_tree_astype
        with pytest.raises(TypeError):
            TreeEstimator(store_tree_astype='failure').fit(X, y)
        with pytest.raises(ValueError):
            TreeEstimator(store_tree_astype='bool').fit(X, y)
        with pytest.raises(ValueError):
            TreeEstimator(store_tree_astype=np.bool_).fit(X, y)

    for name, TreeEstimator in REG_TREES.items():
        # integer types for store_tree_astype with regressor
        with pytest.raises(ValueError):
            TreeEstimator(store_tree_astype=np.uint32).fit(X, y)

    # non positive target for Poisson splitting Criterion
    est = DecisionTreeRegressor(criterion="poisson")
    with pytest.raises(ValueError, match="y is not positive.*Poisson"):
        est.fit([[0, 1, 2]], [0, 0, 0])
    with pytest.raises(ValueError, match="Some.*y are negative.*Poisson"):
        est.fit([[0, 1, 2]], [5, -0.1, 2])


def test_min_samples_split():
    """Test min_samples_split parameter"""
    X = np.asfortranarray(iris.data, dtype=tree._tree.DTYPE)
    y = iris.target

    # test both DepthFirstTreeBuilder and BestFirstTreeBuilder
    # by setting max_leaf_nodes
    for max_leaf_nodes, name in product((None, 1000), ALL_TREES.keys()):
        TreeEstimator = ALL_TREES[name]

        # test for integer parameter
        est = TreeEstimator(min_samples_split=10,
                            max_leaf_nodes=max_leaf_nodes,
                            random_state=0)
        est.fit(X, y)
        # count samples on nodes, -1 means it is a leaf
        node_samples = est.tree_.n_node_samples[est.tree_.children_left != -1]

        assert np.min(node_samples) > 9, "Failed with {0}".format(name)

        # test for float parameter
        est = TreeEstimator(min_samples_split=0.2,
                            max_leaf_nodes=max_leaf_nodes,
                            random_state=0)
        est.fit(X, y)
        # count samples on nodes, -1 means it is a leaf
        node_samples = est.tree_.n_node_samples[est.tree_.children_left != -1]

        assert np.min(node_samples) > 9, "Failed with {0}".format(name)


def test_min_samples_leaf():
    # Test if leaves contain more than leaf_count training examples
    X = np.asfortranarray(iris.data, dtype=tree._tree.DTYPE)
    y = iris.target

    # test both DepthFirstTreeBuilder and BestFirstTreeBuilder
    # by setting max_leaf_nodes
    for max_leaf_nodes, name in product((None, 1000), ALL_TREES.keys()):
        TreeEstimator = ALL_TREES[name]

        # test integer parameter
        est = TreeEstimator(min_samples_leaf=5,
                            max_leaf_nodes=max_leaf_nodes,
                            random_state=0)
        est.fit(X, y)
        out = est.tree_.apply(X)
        node_counts = np.bincount(out)
        # drop inner nodes
        leaf_count = node_counts[node_counts != 0]
        assert np.min(leaf_count) > 4, "Failed with {0}".format(name)

        # test float parameter
        est = TreeEstimator(min_samples_leaf=0.1,
                            max_leaf_nodes=max_leaf_nodes,
                            random_state=0)
        est.fit(X, y)
        out = est.tree_.apply(X)
        node_counts = np.bincount(out)
        # drop inner nodes
        leaf_count = node_counts[node_counts != 0]
        assert np.min(leaf_count) > 4, "Failed with {0}".format(name)


def check_min_weight_fraction_leaf(name, datasets, sparse=False):
    """Test if leaves contain at least min_weight_fraction_leaf of the
    training set"""
    if sparse:
        X = DATASETS[datasets]["X_sparse"].astype(np.float32)
    else:
        X = DATASETS[datasets]["X"].astype(np.float32)
    y = DATASETS[datasets]["y"]

    weights = rng.rand(X.shape[0])
    total_weight = np.sum(weights)

    TreeEstimator = ALL_TREES[name]

    # test both DepthFirstTreeBuilder and BestFirstTreeBuilder
    # by setting max_leaf_nodes
    for max_leaf_nodes, frac in product((None, 1000), np.linspace(0, 0.5, 6)):
        est = TreeEstimator(min_weight_fraction_leaf=frac,
                            max_leaf_nodes=max_leaf_nodes,
                            random_state=0)
        est.fit(X, y, sample_weight=weights)

        if sparse:
            out = est.tree_.apply(X.tocsr())

        else:
            out = est.tree_.apply(X)

        node_weights = np.bincount(out, weights=weights)
        # drop inner nodes
        leaf_weights = node_weights[node_weights != 0]
        assert (
            np.min(leaf_weights) >=
            total_weight * est.min_weight_fraction_leaf), (
                "Failed with {0} min_weight_fraction_leaf={1}".format(
                    name, est.min_weight_fraction_leaf))

    # test case with no weights passed in
    total_weight = X.shape[0]

    for max_leaf_nodes, frac in product((None, 1000), np.linspace(0, 0.5, 6)):
        est = TreeEstimator(min_weight_fraction_leaf=frac,
                            max_leaf_nodes=max_leaf_nodes,
                            random_state=0)
        est.fit(X, y)

        if sparse:
            out = est.tree_.apply(X.tocsr())
        else:
            out = est.tree_.apply(X)

        node_weights = np.bincount(out)
        # drop inner nodes
        leaf_weights = node_weights[node_weights != 0]
        assert (
            np.min(leaf_weights) >=
            total_weight * est.min_weight_fraction_leaf), (
                "Failed with {0} min_weight_fraction_leaf={1}".format(
                    name, est.min_weight_fraction_leaf))


@pytest.mark.parametrize("name", ALL_TREES)
def test_min_weight_fraction_leaf_on_dense_input(name):
    check_min_weight_fraction_leaf(name, "iris")


@pytest.mark.parametrize("name", SPARSE_TREES)
def test_min_weight_fraction_leaf_on_sparse_input(name):
    check_min_weight_fraction_leaf(name, "multilabel", True)


def check_min_weight_fraction_leaf_with_min_samples_leaf(name, datasets,
                                                         sparse=False):
    """Test the interaction between min_weight_fraction_leaf and
    min_samples_leaf when sample_weights is not provided in fit."""
    if sparse:
        X = DATASETS[datasets]["X_sparse"].astype(np.float32)
    else:
        X = DATASETS[datasets]["X"].astype(np.float32)
    y = DATASETS[datasets]["y"]

    total_weight = X.shape[0]
    TreeEstimator = ALL_TREES[name]
    for max_leaf_nodes, frac in product((None, 1000), np.linspace(0, 0.5, 3)):
        # test integer min_samples_leaf
        est = TreeEstimator(min_weight_fraction_leaf=frac,
                            max_leaf_nodes=max_leaf_nodes,
                            min_samples_leaf=5,
                            random_state=0)
        est.fit(X, y)

        if sparse:
            out = est.tree_.apply(X.tocsr())
        else:
            out = est.tree_.apply(X)

        node_weights = np.bincount(out)
        # drop inner nodes
        leaf_weights = node_weights[node_weights != 0]
        assert (
            np.min(leaf_weights) >=
            max((total_weight *
                 est.min_weight_fraction_leaf), 5)), (
                     "Failed with {0} min_weight_fraction_leaf={1}, "
                     "min_samples_leaf={2}".format(
                         name, est.min_weight_fraction_leaf,
                         est.min_samples_leaf))
    for max_leaf_nodes, frac in product((None, 1000), np.linspace(0, 0.5, 3)):
        # test float min_samples_leaf
        est = TreeEstimator(min_weight_fraction_leaf=frac,
                            max_leaf_nodes=max_leaf_nodes,
                            min_samples_leaf=.1,
                            random_state=0)
        est.fit(X, y)

        if sparse:
            out = est.tree_.apply(X.tocsr())
        else:
            out = est.tree_.apply(X)

        node_weights = np.bincount(out)
        # drop inner nodes
        leaf_weights = node_weights[node_weights != 0]
        assert (
            np.min(leaf_weights) >=
            max((total_weight * est.min_weight_fraction_leaf),
                (total_weight * est.min_samples_leaf))), (
                    "Failed with {0} min_weight_fraction_leaf={1}, "
                    "min_samples_leaf={2}".format(name,
                                                  est.min_weight_fraction_leaf,
                                                  est.min_samples_leaf))


@pytest.mark.parametrize("name", ALL_TREES)
def test_min_weight_fraction_leaf_with_min_samples_leaf_on_dense_input(name):
    check_min_weight_fraction_leaf_with_min_samples_leaf(name, "iris")


@pytest.mark.parametrize("name", SPARSE_TREES)
def test_min_weight_fraction_leaf_with_min_samples_leaf_on_sparse_input(name):
    check_min_weight_fraction_leaf_with_min_samples_leaf(
            name, "multilabel", True)


def test_min_impurity_split():
    # test if min_impurity_split creates leaves with impurity
    # [0, min_impurity_split) when min_samples_leaf = 1 and
    # min_samples_split = 2.
    X = np.asfortranarray(iris.data, dtype=tree._tree.DTYPE)
    y = iris.target

    # test both DepthFirstTreeBuilder and BestFirstTreeBuilder
    # by setting max_leaf_nodes
    for max_leaf_nodes, name in product((None, 1000), ALL_TREES.keys()):
        TreeEstimator = ALL_TREES[name]
        min_impurity_split = .5

        # verify leaf nodes without min_impurity_split less than
        # impurity 1e-7
        est = TreeEstimator(max_leaf_nodes=max_leaf_nodes,
                            random_state=0)
        assert est.min_impurity_split is None, (
            "Failed, min_impurity_split = {0} != None".format(
                est.min_impurity_split))
        try:
            assert_warns(FutureWarning, est.fit, X, y)
        except AssertionError:
            pass
        for node in range(est.tree_.node_count):
            if (est.tree_.children_left[node] == TREE_LEAF or
                    est.tree_.children_right[node] == TREE_LEAF):
                assert est.tree_.impurity[node] == 0., (
                    "Failed with {0} min_impurity_split={1}".format(
                        est.tree_.impurity[node],
                        est.min_impurity_split))

        # verify leaf nodes have impurity [0,min_impurity_split] when using
        # min_impurity_split
        est = TreeEstimator(max_leaf_nodes=max_leaf_nodes,
                            min_impurity_split=min_impurity_split,
                            random_state=0)
        assert_warns_message(FutureWarning,
                             "Use the min_impurity_decrease",
                             est.fit, X, y)
        for node in range(est.tree_.node_count):
            if (est.tree_.children_left[node] == TREE_LEAF or
                    est.tree_.children_right[node] == TREE_LEAF):
                assert est.tree_.impurity[node] >= 0, (
                    "Failed with {0}, min_impurity_split={1}".format(
                        est.tree_.impurity[node],
                        est.min_impurity_split))
                assert est.tree_.impurity[node] <= min_impurity_split, (
                    "Failed with {0}, min_impurity_split={1}".format(
                        est.tree_.impurity[node],
                        est.min_impurity_split))


def test_min_impurity_decrease():
    # test if min_impurity_decrease ensure that a split is made only if
    # if the impurity decrease is atleast that value
    X, y = datasets.make_classification(n_samples=10000, random_state=42)

    # test both DepthFirstTreeBuilder and BestFirstTreeBuilder
    # by setting max_leaf_nodes
    for max_leaf_nodes, name in product((None, 1000), ALL_TREES.keys()):
        TreeEstimator = ALL_TREES[name]

        # Check default value of min_impurity_decrease, 1e-7
        est1 = TreeEstimator(max_leaf_nodes=max_leaf_nodes, random_state=0)
        # Check with explicit value of 0.05
        est2 = TreeEstimator(max_leaf_nodes=max_leaf_nodes,
                             min_impurity_decrease=0.05, random_state=0)
        # Check with a much lower value of 0.0001
        est3 = TreeEstimator(max_leaf_nodes=max_leaf_nodes,
                             min_impurity_decrease=0.0001, random_state=0)
        # Check with a much lower value of 0.1
        est4 = TreeEstimator(max_leaf_nodes=max_leaf_nodes,
                             min_impurity_decrease=0.1, random_state=0)

        for est, expected_decrease in ((est1, 1e-7), (est2, 0.05),
                                       (est3, 0.0001), (est4, 0.1)):
            assert est.min_impurity_decrease <= expected_decrease, (
                "Failed, min_impurity_decrease = {0} > {1}".format(
                    est.min_impurity_decrease,
                    expected_decrease))
            est.fit(X, y)
            for node in range(est.tree_.node_count):
                # If current node is a not leaf node, check if the split was
                # justified w.r.t the min_impurity_decrease
                if est.tree_.children_left[node] != TREE_LEAF:
                    imp_parent = est.tree_.impurity[node]
                    wtd_n_node = est.tree_.weighted_n_node_samples[node]

                    left = est.tree_.children_left[node]
                    wtd_n_left = est.tree_.weighted_n_node_samples[left]
                    imp_left = est.tree_.impurity[left]
                    wtd_imp_left = wtd_n_left * imp_left

                    right = est.tree_.children_right[node]
                    wtd_n_right = est.tree_.weighted_n_node_samples[right]
                    imp_right = est.tree_.impurity[right]
                    wtd_imp_right = wtd_n_right * imp_right

                    wtd_avg_left_right_imp = wtd_imp_right + wtd_imp_left
                    wtd_avg_left_right_imp /= wtd_n_node

                    fractional_node_weight = (
                        est.tree_.weighted_n_node_samples[node] / X.shape[0])

                    actual_decrease = fractional_node_weight * (
                        imp_parent - wtd_avg_left_right_imp)

                    assert actual_decrease >= expected_decrease, (
                        "Failed with {0} expected min_impurity_decrease={1}"
                        .format(actual_decrease,
                                expected_decrease))

    for name, TreeEstimator in ALL_TREES.items():
        if "Classifier" in name:
            X, y = iris.data, iris.target
        else:
            X, y = diabetes.data, diabetes.target

        est = TreeEstimator(random_state=0)
        est.fit(X, y)
        score = est.score(X, y)
        fitted_attribute = dict()
        for attribute in ["max_depth", "node_count", "capacity"]:
            fitted_attribute[attribute] = getattr(est.tree_, attribute)

        serialized_object = pickle.dumps(est)
        est2 = pickle.loads(serialized_object)
        assert type(est2) == est.__class__
        score2 = est2.score(X, y)
        assert score == score2, (
            "Failed to generate same score  after pickling "
            "with {0}".format(name))

        for attribute in fitted_attribute:
            assert (getattr(est2.tree_, attribute) ==
                    fitted_attribute[attribute]), (
                        "Failed to generate same attribute {0} after "
                        "pickling with {1}".format(attribute, name))


@pytest.mark.parametrize('tree_value_dtype', CLF_TREE_VALUE_DTYPES)
def test_multioutput(tree_value_dtype):
    # Check estimators on multi-output problems.
    X = [[-2, -1],
         [-1, -1],
         [-1, -2],
         [1, 1],
         [1, 2],
         [2, 1],
         [-2, 1],
         [-1, 1],
         [-1, 2],
         [2, -1],
         [1, -1],
         [1, -2]]

    y = [[-1, 0],
         [-1, 0],
         [-1, 0],
         [1, 1],
         [1, 1],
         [1, 1],
         [-1, 2],
         [-1, 2],
         [-1, 2],
         [1, 3],
         [1, 3],
         [1, 3]]

    T = [[-1, -1], [1, 1], [-1, 1], [1, -1]]
    y_true = [[-1, 0], [1, 1], [-1, 2], [1, 3]]

    # toy classification problem
    for name, TreeClassifier in CLF_TREES.items():
        clf = TreeClassifier(random_state=0,
                             store_tree_astype=tree_value_dtype)
        y_hat = clf.fit(X, y).predict(T)
        assert_array_equal(y_hat, y_true)
        assert y_hat.shape == (4, 2)

        proba = clf.predict_proba(T)
        assert len(proba) == 2
        assert proba[0].shape == (4, 2)
        assert proba[1].shape == (4, 4)
        assert proba[0].dtype == np.float64
        assert proba[1].dtype == np.float64

        log_proba = clf.predict_log_proba(T)
        assert len(log_proba) == 2
        assert log_proba[0].shape == (4, 2)
        assert log_proba[1].shape == (4, 4)
        assert log_proba[0].dtype == np.float64
        assert log_proba[1].dtype == np.float64

    # toy regression problem
    if tree_value_dtype in REG_TREE_VALUE_DTYPES:
        for name, TreeRegressor in REG_TREES.items():
            reg = TreeRegressor(random_state=0,
                                store_tree_astype=tree_value_dtype)
            y_hat = reg.fit(X, y).predict(T)
            assert_almost_equal(y_hat, y_true)
            assert y_hat.shape == (4, 2)
            assert y_hat.dtype == np.float64


def test_classes_shape():
    # Test that n_classes_ and classes_ have proper shape.
    for name, TreeClassifier in CLF_TREES.items():
        # Classification, single output
        clf = TreeClassifier(random_state=0)
        clf.fit(X, y)

        assert clf.n_classes_ == 2
        assert_array_equal(clf.classes_, [-1, 1])

        # Classification, multi-output
        _y = np.vstack((y, np.array(y) * 2)).T
        clf = TreeClassifier(random_state=0)
        clf.fit(X, _y)
        assert len(clf.n_classes_) == 2
        assert len(clf.classes_) == 2
        assert_array_equal(clf.n_classes_, [2, 2])
        assert_array_equal(clf.classes_, [[-1, 1], [-2, 2]])


def test_unbalanced_iris():
    # Check class rebalancing.
    unbalanced_X = iris.data[:125]
    unbalanced_y = iris.target[:125]
    sample_weight = compute_sample_weight("balanced", unbalanced_y)

    for name, TreeClassifier in CLF_TREES.items():
        clf = TreeClassifier(random_state=0)
        clf.fit(unbalanced_X, unbalanced_y, sample_weight=sample_weight)
        assert_almost_equal(clf.predict(unbalanced_X), unbalanced_y)

@pytest.mark.parametrize('tree_value_dtype', REG_TREE_VALUE_DTYPES)
def test_memory_layout(tree_value_dtype):
    # Check that it works no matter the memory layout
    for (name, TreeEstimator), dtype in product(ALL_TREES.items(),
                                                [np.float64, np.float32]):
        est = TreeEstimator(random_state=0, store_tree_astype=tree_value_dtype)

        # Nothing
        X = np.asarray(iris.data, dtype=dtype)
        y = iris.target
        assert_array_equal(est.fit(X, y).predict(X), y)

        # C-order
        X = np.asarray(iris.data, order="C", dtype=dtype)
        y = iris.target
        assert_array_equal(est.fit(X, y).predict(X), y)

        # F-order
        X = np.asarray(iris.data, order="F", dtype=dtype)
        y = iris.target
        assert_array_equal(est.fit(X, y).predict(X), y)

        # Contiguous
        X = np.ascontiguousarray(iris.data, dtype=dtype)
        y = iris.target
        assert_array_equal(est.fit(X, y).predict(X), y)

        # csr matrix
        X = csr_matrix(iris.data, dtype=dtype)
        y = iris.target
        assert_array_equal(est.fit(X, y).predict(X), y)

        # csc_matrix
        X = csc_matrix(iris.data, dtype=dtype)
        y = iris.target
        assert_array_equal(est.fit(X, y).predict(X), y)

        # Strided
        X = np.asarray(iris.data[::3], dtype=dtype)
        y = iris.target[::3]
        assert_array_equal(est.fit(X, y).predict(X), y)


def test_sample_weight():
    # Check sample weighting.
    # Test that zero-weighted samples are not taken into account
    X = np.arange(100)[:, np.newaxis]
    y = np.ones(100)
    y[:50] = 0.0

    sample_weight = np.ones(100)
    sample_weight[y == 0] = 0.0

    clf = DecisionTreeClassifier(random_state=0)
    clf.fit(X, y, sample_weight=sample_weight)
    assert_array_equal(clf.predict(X), np.ones(100))

    # Test that low weighted samples are not taken into account at low depth
    X = np.arange(200)[:, np.newaxis]
    y = np.zeros(200)
    y[50:100] = 1
    y[100:200] = 2
    X[100:200, 0] = 200

    sample_weight = np.ones(200)

    sample_weight[y == 2] = .51  # Samples of class '2' are still weightier
    clf = DecisionTreeClassifier(max_depth=1, random_state=0)
    clf.fit(X, y, sample_weight=sample_weight)
    assert clf.tree_.threshold[0] == 149.5

    sample_weight[y == 2] = .5  # Samples of class '2' are no longer weightier
    clf = DecisionTreeClassifier(max_depth=1, random_state=0)
    clf.fit(X, y, sample_weight=sample_weight)
    assert clf.tree_.threshold[0] == 49.5  # Threshold should have moved

    # Test that sample weighting is the same as having duplicates
    X = iris.data
    y = iris.target

    duplicates = rng.randint(0, X.shape[0], 100)

    clf = DecisionTreeClassifier(random_state=1)
    clf.fit(X[duplicates], y[duplicates])

    sample_weight = np.bincount(duplicates, minlength=X.shape[0])
    clf2 = DecisionTreeClassifier(random_state=1)
    clf2.fit(X, y, sample_weight=sample_weight)

    internal = clf.tree_.children_left != tree._tree.TREE_LEAF
    assert_array_almost_equal(clf.tree_.threshold[internal],
                              clf2.tree_.threshold[internal])


def test_sample_weight_invalid():
    # Check sample weighting raises errors.
    X = np.arange(100)[:, np.newaxis]
    y = np.ones(100)
    y[:50] = 0.0

    clf = DecisionTreeClassifier(random_state=0)

    sample_weight = np.random.rand(100, 1)
    with pytest.raises(ValueError):
        clf.fit(X, y, sample_weight=sample_weight)

    sample_weight = np.array(0)
    expected_err = r"Singleton.* cannot be considered a valid collection"
    with pytest.raises(TypeError, match=expected_err):
        clf.fit(X, y, sample_weight=sample_weight)


def check_class_weights(name):
    """Check class_weights resemble sample_weights behavior."""
    TreeClassifier = CLF_TREES[name]

    # Iris is balanced, so no effect expected for using 'balanced' weights
    clf1 = TreeClassifier(random_state=0)
    clf1.fit(iris.data, iris.target)
    clf2 = TreeClassifier(class_weight='balanced', random_state=0)
    clf2.fit(iris.data, iris.target)
    assert_almost_equal(clf1.feature_importances_, clf2.feature_importances_)

    # Make a multi-output problem with three copies of Iris
    iris_multi = np.vstack((iris.target, iris.target, iris.target)).T
    # Create user-defined weights that should balance over the outputs
    clf3 = TreeClassifier(class_weight=[{0: 2., 1: 2., 2: 1.},
                                        {0: 2., 1: 1., 2: 2.},
                                        {0: 1., 1: 2., 2: 2.}],
                          random_state=0)
    clf3.fit(iris.data, iris_multi)
    assert_almost_equal(clf2.feature_importances_, clf3.feature_importances_)
    # Check against multi-output "auto" which should also have no effect
    clf4 = TreeClassifier(class_weight='balanced', random_state=0)
    clf4.fit(iris.data, iris_multi)
    assert_almost_equal(clf3.feature_importances_, clf4.feature_importances_)

    # Inflate importance of class 1, check against user-defined weights
    sample_weight = np.ones(iris.target.shape)
    sample_weight[iris.target == 1] *= 100
    class_weight = {0: 1., 1: 100., 2: 1.}
    clf1 = TreeClassifier(random_state=0)
    clf1.fit(iris.data, iris.target, sample_weight)
    clf2 = TreeClassifier(class_weight=class_weight, random_state=0)
    clf2.fit(iris.data, iris.target)
    assert_almost_equal(clf1.feature_importances_, clf2.feature_importances_)

    # Check that sample_weight and class_weight are multiplicative
    clf1 = TreeClassifier(random_state=0)
    clf1.fit(iris.data, iris.target, sample_weight ** 2)
    clf2 = TreeClassifier(class_weight=class_weight, random_state=0)
    clf2.fit(iris.data, iris.target, sample_weight)
    assert_almost_equal(clf1.feature_importances_, clf2.feature_importances_)


@pytest.mark.parametrize("name", CLF_TREES)
def test_class_weights(name):
    check_class_weights(name)


def check_class_weight_errors(name):
    # Test if class_weight raises errors and warnings when expected.
    TreeClassifier = CLF_TREES[name]
    _y = np.vstack((y, np.array(y) * 2)).T

    # Invalid preset string
    clf = TreeClassifier(class_weight='the larch', random_state=0)
    with pytest.raises(ValueError):
        clf.fit(X, y)
    with pytest.raises(ValueError):
        clf.fit(X, _y)

    # Not a list or preset for multi-output
    clf = TreeClassifier(class_weight=1, random_state=0)
    with pytest.raises(ValueError):
        clf.fit(X, _y)

    # Incorrect length list for multi-output
    clf = TreeClassifier(class_weight=[{-1: 0.5, 1: 1.}], random_state=0)
    with pytest.raises(ValueError):
        clf.fit(X, _y)


@pytest.mark.parametrize("name", CLF_TREES)
def test_class_weight_errors(name):
    check_class_weight_errors(name)


def test_max_leaf_nodes():
    # Test greedy trees with max_depth + 1 leafs.
    X, y = datasets.make_hastie_10_2(n_samples=100, random_state=1)
    k = 4
    for name, TreeEstimator in ALL_TREES.items():
        est = TreeEstimator(max_depth=None, max_leaf_nodes=k + 1).fit(X, y)
        assert est.get_n_leaves() == k + 1

        # max_leaf_nodes in (0, 1) should raise ValueError
        est = TreeEstimator(max_depth=None, max_leaf_nodes=0)
        with pytest.raises(ValueError):
            est.fit(X, y)
        est = TreeEstimator(max_depth=None, max_leaf_nodes=1)
        with pytest.raises(ValueError):
            est.fit(X, y)
        est = TreeEstimator(max_depth=None, max_leaf_nodes=0.1)
        with pytest.raises(ValueError):
            est.fit(X, y)


def test_max_leaf_nodes_max_depth():
    # Test precedence of max_leaf_nodes over max_depth.
    X, y = datasets.make_hastie_10_2(n_samples=100, random_state=1)
    k = 4
    for name, TreeEstimator in ALL_TREES.items():
        est = TreeEstimator(max_depth=1, max_leaf_nodes=k).fit(X, y)
        assert est.get_depth() == 1


def test_arrays_persist():
    # Ensure property arrays' memory stays alive when tree disappears
    # non-regression for #2726
    for attr in ['n_classes', 'value', 'children_left', 'children_right',
                 'threshold', 'impurity', 'feature', 'n_node_samples']:
        value = getattr(DecisionTreeClassifier().fit([[0], [1]],
                                                     [0, 1]).tree_, attr)
        # if pointing to freed memory, contents may be arbitrary
        assert -3 <= value.flat[0] < 3, \
            'Array points to arbitrary memory'


def test_only_constant_features():
    random_state = check_random_state(0)
    X = np.zeros((10, 20))
    y = random_state.randint(0, 2, (10, ))
    for name, TreeEstimator in ALL_TREES.items():
        est = TreeEstimator(random_state=0)
        est.fit(X, y)
        assert est.tree_.max_depth == 0


def test_behaviour_constant_feature_after_splits():
    X = np.transpose(np.vstack(([[0, 0, 0, 0, 0, 1, 2, 4, 5, 6, 7]],
                               np.zeros((4, 11)))))
    y = [0, 0, 0, 1, 1, 2, 2, 2, 3, 3, 3]
    for name, TreeEstimator in ALL_TREES.items():
        # do not check extra random trees
        if "ExtraTree" not in name:
            est = TreeEstimator(random_state=0, max_features=1)
            est.fit(X, y)
            assert est.tree_.max_depth == 2
            assert est.tree_.node_count == 5


def test_with_only_one_non_constant_features():
    X = np.hstack([np.array([[1.], [1.], [0.], [0.]]),
                   np.zeros((4, 1000))])

    y = np.array([0., 1., 0., 1.0])
    for name, TreeEstimator in CLF_TREES.items():
        est = TreeEstimator(random_state=0, max_features=1)
        est.fit(X, y)
        assert est.tree_.max_depth == 1
        assert_array_equal(est.predict_proba(X), np.full((4, 2), 0.5))

    for name, TreeEstimator in REG_TREES.items():
        est = TreeEstimator(random_state=0, max_features=1)
        est.fit(X, y)
        assert est.tree_.max_depth == 1
        assert_array_equal(est.predict(X), np.full((4, ), 0.5))


def test_big_input():
    # Test if the warning for too large inputs is appropriate.
    X = np.repeat(10 ** 40., 4).astype(np.float64).reshape(-1, 1)
    clf = DecisionTreeClassifier()
    try:
        clf.fit(X, [0, 1, 0, 1])
    except ValueError as e:
        assert "float32" in str(e)


def test_realloc():
    from sklearn.tree._utils import _realloc_test
    with pytest.raises(MemoryError):
        _realloc_test()


def test_huge_allocations():
    n_bits = 8 * struct.calcsize("P")

    X = np.random.randn(10, 2)
    y = np.random.randint(0, 2, 10)

    # Sanity check: we cannot request more memory than the size of the address
    # space. Currently raises OverflowError.
    huge = 2 ** (n_bits + 1)
    clf = DecisionTreeClassifier(splitter='best', max_leaf_nodes=huge)
    with pytest.raises(Exception):
        clf.fit(X, y)

    # Non-regression test: MemoryError used to be dropped by Cython
    # because of missing "except *".
    huge = 2 ** (n_bits - 1) - 1
    clf = DecisionTreeClassifier(splitter='best', max_leaf_nodes=huge)
    with pytest.raises(MemoryError):
        clf.fit(X, y)


def check_sparse_input(tree, dataset, tree_value_dtype, max_depth=None):
    TreeEstimator = ALL_TREES[tree]
    X = DATASETS[dataset]["X"]
    X_sparse = DATASETS[dataset]["X_sparse"]
    y = DATASETS[dataset]["y"]

    # Gain testing time
    if dataset in ["digits", "diabetes"]:
        n_samples = X.shape[0] // 5
        X = X[:n_samples]
        X_sparse = X_sparse[:n_samples]
        y = y[:n_samples]

    for sparse_format in (csr_matrix, csc_matrix, coo_matrix):
        X_sparse = sparse_format(X_sparse)

        # Check the default (depth first search)
        d = TreeEstimator(
            random_state=0, max_depth=max_depth,
            store_tree_astype=tree_value_dtype).fit(X, y)
        s = TreeEstimator(
            random_state=0, max_depth=max_depth,
            store_tree_astype=tree_value_dtype).fit(X_sparse, y)

        assert_tree_equal(d.tree_, s.tree_,
                          "{0} with dense and sparse format gave different "
                          "trees".format(tree))

        y_pred = d.predict(X)
        if tree in CLF_TREES:
            y_proba = d.predict_proba(X)
            y_log_proba = d.predict_log_proba(X)

        for sparse_matrix in (csr_matrix, csc_matrix, coo_matrix):
            X_sparse_test = sparse_matrix(X_sparse, dtype=np.float32)

            assert_array_almost_equal(s.predict(X_sparse_test), y_pred)

            if tree in CLF_TREES:
                assert_array_almost_equal(s.predict_proba(X_sparse_test),
                                          y_proba)
                assert_array_almost_equal(s.predict_log_proba(X_sparse_test),
                                          y_log_proba)


@pytest.mark.parametrize("tree_type", SPARSE_TREES)
@pytest.mark.parametrize(
        "dataset",
        ("clf_small", "toy", "digits", "multilabel",
         "sparse-pos", "sparse-neg", "sparse-mix",
         "zeros")
)
@pytest.mark.parametrize('tree_value_dtype', REG_TREE_VALUE_DTYPES)
def test_sparse_input(tree_type, dataset, tree_value_dtype):
    max_depth = 3 if dataset == "digits" else None
    check_sparse_input(tree_type, dataset, tree_value_dtype, max_depth)


@pytest.mark.parametrize("tree_type",
                         sorted(set(SPARSE_TREES).intersection(REG_TREES)))
@pytest.mark.parametrize("dataset", ["diabetes", "reg_small"])
@pytest.mark.parametrize('tree_value_dtype', REG_TREE_VALUE_DTYPES)
def test_sparse_input_reg_trees(tree_type, dataset, tree_value_dtype):
    # Due to numerical instability of MSE and too strict test, we limit the
    # maximal depth
    check_sparse_input(tree_type, dataset, tree_value_dtype, 2)


def check_sparse_parameters(tree, dataset):
    TreeEstimator = ALL_TREES[tree]
    X = DATASETS[dataset]["X"]
    X_sparse = DATASETS[dataset]["X_sparse"]
    y = DATASETS[dataset]["y"]

    # Check max_features
    d = TreeEstimator(random_state=0, max_features=1, max_depth=2).fit(X, y)
    s = TreeEstimator(random_state=0, max_features=1,
                      max_depth=2).fit(X_sparse, y)
    assert_tree_equal(d.tree_, s.tree_,
                      "{0} with dense and sparse format gave different "
                      "trees".format(tree))
    assert_array_almost_equal(s.predict(X), d.predict(X))

    # Check min_samples_split
    d = TreeEstimator(random_state=0, max_features=1,
                      min_samples_split=10).fit(X, y)
    s = TreeEstimator(random_state=0, max_features=1,
                      min_samples_split=10).fit(X_sparse, y)
    assert_tree_equal(d.tree_, s.tree_,
                      "{0} with dense and sparse format gave different "
                      "trees".format(tree))
    assert_array_almost_equal(s.predict(X), d.predict(X))

    # Check min_samples_leaf
    d = TreeEstimator(random_state=0,
                      min_samples_leaf=X_sparse.shape[0] // 2).fit(X, y)
    s = TreeEstimator(random_state=0,
                      min_samples_leaf=X_sparse.shape[0] // 2).fit(X_sparse, y)
    assert_tree_equal(d.tree_, s.tree_,
                      "{0} with dense and sparse format gave different "
                      "trees".format(tree))
    assert_array_almost_equal(s.predict(X), d.predict(X))

    # Check best-first search
    d = TreeEstimator(random_state=0, max_leaf_nodes=3).fit(X, y)
    s = TreeEstimator(random_state=0, max_leaf_nodes=3).fit(X_sparse, y)
    assert_tree_equal(d.tree_, s.tree_,
                      "{0} with dense and sparse format gave different "
                      "trees".format(tree))
    assert_array_almost_equal(s.predict(X), d.predict(X))


def check_sparse_criterion(tree, dataset):
    TreeEstimator = ALL_TREES[tree]
    X = DATASETS[dataset]["X"]
    X_sparse = DATASETS[dataset]["X_sparse"]
    y = DATASETS[dataset]["y"]

    # Check various criterion
    CRITERIONS = REG_CRITERIONS if tree in REG_TREES else CLF_CRITERIONS
    for criterion in CRITERIONS:
        d = TreeEstimator(random_state=0, max_depth=3,
                          criterion=criterion).fit(X, y)
        s = TreeEstimator(random_state=0, max_depth=3,
                          criterion=criterion).fit(X_sparse, y)

        assert_tree_equal(d.tree_, s.tree_,
                          "{0} with dense and sparse format gave different "
                          "trees".format(tree))
        assert_array_almost_equal(s.predict(X), d.predict(X))


@pytest.mark.parametrize("tree_type", SPARSE_TREES)
@pytest.mark.parametrize("dataset",
                         ["sparse-pos", "sparse-neg", "sparse-mix", "zeros"])
@pytest.mark.parametrize("check",
                         [check_sparse_parameters, check_sparse_criterion])
def test_sparse(tree_type, dataset, check):
    check(tree_type, dataset)


def check_explicit_sparse_zeros(tree, max_depth=3,
                                n_features=10):
    TreeEstimator = ALL_TREES[tree]

    # n_samples set n_feature to ease construction of a simultaneous
    # construction of a csr and csc matrix
    n_samples = n_features
    samples = np.arange(n_samples)

    # Generate X, y
    random_state = check_random_state(0)
    indices = []
    data = []
    offset = 0
    indptr = [offset]
    for i in range(n_features):
        n_nonzero_i = random_state.binomial(n_samples, 0.5)
        indices_i = random_state.permutation(samples)[:n_nonzero_i]
        indices.append(indices_i)
        data_i = random_state.binomial(3, 0.5, size=(n_nonzero_i, )) - 1
        data.append(data_i)
        offset += n_nonzero_i
        indptr.append(offset)

    indices = np.concatenate(indices)
    data = np.array(np.concatenate(data), dtype=np.float32)
    X_sparse = csc_matrix((data, indices, indptr),
                          shape=(n_samples, n_features))
    X = X_sparse.toarray()
    X_sparse_test = csr_matrix((data, indices, indptr),
                               shape=(n_samples, n_features))
    X_test = X_sparse_test.toarray()
    y = random_state.randint(0, 3, size=(n_samples, ))

    # Ensure that X_sparse_test owns its data, indices and indptr array
    X_sparse_test = X_sparse_test.copy()

    # Ensure that we have explicit zeros
    assert (X_sparse.data == 0.).sum() > 0
    assert (X_sparse_test.data == 0.).sum() > 0

    # Perform the comparison
    d = TreeEstimator(random_state=0, max_depth=max_depth).fit(X, y)
    s = TreeEstimator(random_state=0, max_depth=max_depth).fit(X_sparse, y)

    assert_tree_equal(d.tree_, s.tree_,
                      "{0} with dense and sparse format gave different "
                      "trees".format(tree))

    Xs = (X_test, X_sparse_test)
    for X1, X2 in product(Xs, Xs):
        assert_array_almost_equal(s.tree_.apply(X1), d.tree_.apply(X2))
        assert_array_almost_equal(s.apply(X1), d.apply(X2))
        assert_array_almost_equal(s.apply(X1), s.tree_.apply(X1))

        assert_array_almost_equal(s.tree_.decision_path(X1).toarray(),
                                  d.tree_.decision_path(X2).toarray())
        assert_array_almost_equal(s.decision_path(X1).toarray(),
                                  d.decision_path(X2).toarray())
        assert_array_almost_equal(s.decision_path(X1).toarray(),
                                  s.tree_.decision_path(X1).toarray())

        assert_array_almost_equal(s.predict(X1), d.predict(X2))

        if tree in CLF_TREES:
            assert_array_almost_equal(s.predict_proba(X1),
                                      d.predict_proba(X2))


@pytest.mark.parametrize("tree_type", SPARSE_TREES)
def test_explicit_sparse_zeros(tree_type):
    check_explicit_sparse_zeros(tree_type)


@ignore_warnings
def check_raise_error_on_1d_input(name):
    TreeEstimator = ALL_TREES[name]

    X = iris.data[:, 0].ravel()
    X_2d = iris.data[:, 0].reshape((-1, 1))
    y = iris.target

    with pytest.raises(ValueError):
        TreeEstimator(random_state=0).fit(X, y)

    est = TreeEstimator(random_state=0)
    est.fit(X_2d, y)
    with pytest.raises(ValueError):
        est.predict([X])


@pytest.mark.parametrize("name", ALL_TREES)
def test_1d_input(name):
    with ignore_warnings():
        check_raise_error_on_1d_input(name)


def _check_min_weight_leaf_split_level(TreeEstimator, X, y, sample_weight):
    est = TreeEstimator(random_state=0)
    est.fit(X, y, sample_weight=sample_weight)
    assert est.tree_.max_depth == 1

    est = TreeEstimator(random_state=0, min_weight_fraction_leaf=0.4)
    est.fit(X, y, sample_weight=sample_weight)
    assert est.tree_.max_depth == 0


def check_min_weight_leaf_split_level(name):
    TreeEstimator = ALL_TREES[name]

    X = np.array([[0], [0], [0], [0], [1]])
    y = [0, 0, 0, 0, 1]
    sample_weight = [0.2, 0.2, 0.2, 0.2, 0.2]
    _check_min_weight_leaf_split_level(TreeEstimator, X, y, sample_weight)

    _check_min_weight_leaf_split_level(TreeEstimator, csc_matrix(X), y,
                                       sample_weight)


@pytest.mark.parametrize("name", ALL_TREES)
def test_min_weight_leaf_split_level(name):
    check_min_weight_leaf_split_level(name)


def check_public_apply(name, tree_value_dtype):
    X_small32 = X_small.astype(tree._tree.DTYPE, copy=False)

    est = ALL_TREES[name](store_tree_astype=tree_value_dtype)
    est.fit(X_small, y_small)
    assert_array_equal(est.apply(X_small),
                       est.tree_.apply(X_small32))


def check_public_apply_sparse(name, tree_value_dtype):
    X_small32 = csr_matrix(X_small.astype(tree._tree.DTYPE, copy=False))

    est = ALL_TREES[name](store_tree_astype=tree_value_dtype)
    est.fit(X_small, y_small)
    assert_array_equal(est.apply(X_small),
                       est.tree_.apply(X_small32))


@pytest.mark.parametrize("name", ALL_TREES)
@pytest.mark.parametrize('tree_value_dtype', REG_TREE_VALUE_DTYPES)
def test_public_apply_all_trees(name, tree_value_dtype):
    check_public_apply(name, tree_value_dtype)


@pytest.mark.parametrize("name", SPARSE_TREES)
@pytest.mark.parametrize('tree_value_dtype', REG_TREE_VALUE_DTYPES)
def test_public_apply_sparse_trees(name, tree_value_dtype):
    check_public_apply_sparse(name, tree_value_dtype)


def test_decision_path_hardcoded():
    X = iris.data
    y = iris.target
    est = DecisionTreeClassifier(random_state=0, max_depth=1).fit(X, y)
    node_indicator = est.decision_path(X[:2]).toarray()
    assert_array_equal(node_indicator, [[1, 1, 0], [1, 0, 1]])


def check_decision_path(name, tree_value_dtype):
    X = iris.data
    y = iris.target
    n_samples = X.shape[0]

    TreeEstimator = ALL_TREES[name]
    est = TreeEstimator(random_state=0, max_depth=2,
                        store_tree_astype=tree_value_dtype)
    est.fit(X, y)

    node_indicator_csr = est.decision_path(X)
    node_indicator = node_indicator_csr.toarray()
    assert node_indicator.shape == (n_samples, est.tree_.node_count)

    # Assert that leaves index are correct
    leaves = est.apply(X)
    leave_indicator = [node_indicator[i, j] for i, j in enumerate(leaves)]
    assert_array_almost_equal(leave_indicator, np.ones(shape=n_samples))

    # Ensure only one leave node per sample
    all_leaves = est.tree_.children_left == TREE_LEAF
    assert_array_almost_equal(np.dot(node_indicator, all_leaves),
                              np.ones(shape=n_samples))

    # Ensure max depth is consistent with sum of indicator
    max_depth = node_indicator.sum(axis=1).max()
    assert est.tree_.max_depth <= max_depth


@pytest.mark.parametrize("name", ALL_TREES)
@pytest.mark.parametrize('tree_value_dtype', REG_TREE_VALUE_DTYPES)
def test_decision_path(name, tree_value_dtype):
    check_decision_path(name, tree_value_dtype)


def check_no_sparse_y_support(name):
    X, y = X_multilabel, csr_matrix(y_multilabel)
    TreeEstimator = ALL_TREES[name]
    with pytest.raises(TypeError):
        TreeEstimator(random_state=0).fit(X, y)


@pytest.mark.parametrize("name", ALL_TREES)
def test_no_sparse_y_support(name):
    # Currently we don't support sparse y
    check_no_sparse_y_support(name)


def test_mae():
    """Check MAE criterion produces correct results on small toy dataset:

    ------------------
    | X | y | weight |
    ------------------
    | 3 | 3 |  0.1   |
    | 5 | 3 |  0.3   |
    | 8 | 4 |  1.0   |
    | 3 | 6 |  0.6   |
    | 5 | 7 |  0.3   |
    ------------------
    |sum wt:|  2.3   |
    ------------------

    Because we are dealing with sample weights, we cannot find the median by
    simply choosing/averaging the centre value(s), instead we consider the
    median where 50% of the cumulative weight is found (in a y sorted data set)
    . Therefore with regards to this test data, the cumulative weight is >= 50%
    when y = 4.  Therefore:
    Median = 4

    For all the samples, we can get the total error by summing:
    Absolute(Median - y) * weight

    I.e., total error = (Absolute(4 - 3) * 0.1)
                      + (Absolute(4 - 3) * 0.3)
                      + (Absolute(4 - 4) * 1.0)
                      + (Absolute(4 - 6) * 0.6)
                      + (Absolute(4 - 7) * 0.3)
                      = 2.5

    Impurity = Total error / total weight
             = 2.5 / 2.3
             = 1.08695652173913
             ------------------

    From this root node, the next best split is between X values of 3 and 5.
    Thus, we have left and right child nodes:

    LEFT                    RIGHT
    ------------------      ------------------
    | X | y | weight |      | X | y | weight |
    ------------------      ------------------
    | 3 | 3 |  0.1   |      | 5 | 3 |  0.3   |
    | 3 | 6 |  0.6   |      | 8 | 4 |  1.0   |
    ------------------      | 5 | 7 |  0.3   |
    |sum wt:|  0.7   |      ------------------
    ------------------      |sum wt:|  1.6   |
                            ------------------

    Impurity is found in the same way:
    Left node Median = 6
    Total error = (Absolute(6 - 3) * 0.1)
                + (Absolute(6 - 6) * 0.6)
                = 0.3

    Left Impurity = Total error / total weight
            = 0.3 / 0.7
            = 0.428571428571429
            -------------------

    Likewise for Right node:
    Right node Median = 4
    Total error = (Absolute(4 - 3) * 0.3)
                + (Absolute(4 - 4) * 1.0)
                + (Absolute(4 - 7) * 0.3)
                = 1.2

    Right Impurity = Total error / total weight
            = 1.2 / 1.6
            = 0.75
            ------
    """
    dt_mae = DecisionTreeRegressor(random_state=0, criterion="mae",
                                   max_leaf_nodes=2)

    # Test MAE where sample weights are non-uniform (as illustrated above):
    dt_mae.fit(X=[[3], [5], [3], [8], [5]], y=[6, 7, 3, 4, 3],
               sample_weight=[0.6, 0.3, 0.1, 1.0, 0.3])
    assert_allclose(dt_mae.tree_.impurity, [2.5 / 2.3, 0.3 / 0.7, 1.2 / 1.6])
    assert_array_equal(dt_mae.tree_.value.flat, [4.0, 6.0, 4.0])

    # Test MAE where all sample weights are uniform:
    dt_mae.fit(X=[[3], [5], [3], [8], [5]], y=[6, 7, 3, 4, 3],
               sample_weight=np.ones(5))
    assert_array_equal(dt_mae.tree_.impurity, [1.4, 1.5, 4.0 / 3.0])
    assert_array_equal(dt_mae.tree_.value.flat, [4, 4.5, 4.0])

    # Test MAE where a `sample_weight` is not explicitly provided.
    # This is equivalent to providing uniform sample weights, though
    # the internal logic is different:
    dt_mae.fit(X=[[3], [5], [3], [8], [5]], y=[6, 7, 3, 4, 3])
    assert_array_equal(dt_mae.tree_.impurity, [1.4, 1.5, 4.0 / 3.0])
    assert_array_equal(dt_mae.tree_.value.flat, [4, 4.5, 4.0])


def test_criterion_copy():
    # Let's check whether copy of our criterion has the same type
    # and properties as original
    n_outputs = 3
    n_classes = np.arange(3, dtype=np.intp)
    n_samples = 100

    def _pickle_copy(obj):
        return pickle.loads(pickle.dumps(obj))
    for copy_func in [copy.copy, copy.deepcopy, _pickle_copy]:
        for _, typename in CRITERIA_CLF.items():
            criteria = typename(n_outputs, n_classes)
            result = copy_func(criteria).__reduce__()
            typename_, (n_outputs_, n_classes_), _ = result
            assert typename == typename_
            assert n_outputs == n_outputs_
            assert_array_equal(n_classes, n_classes_)

        for _, typename in CRITERIA_REG.items():
            criteria = typename(n_outputs, n_samples)
            result = copy_func(criteria).__reduce__()
            typename_, (n_outputs_, n_samples_), _ = result
            assert typename == typename_
            assert n_outputs == n_outputs_
            assert n_samples == n_samples_


def test_empty_leaf_infinite_threshold():
    # try to make empty leaf by using near infinite value.
    data = np.random.RandomState(0).randn(100, 11) * 2e38
    data = np.nan_to_num(data.astype('float32'))
    X_full = data[:, :-1]
    X_sparse = csc_matrix(X_full)
    y = data[:, -1]
    for X in [X_full, X_sparse]:
        tree = DecisionTreeRegressor(random_state=0).fit(X, y)
        terminal_regions = tree.apply(X)
        left_leaf = set(np.where(tree.tree_.children_left == TREE_LEAF)[0])
        empty_leaf = left_leaf.difference(terminal_regions)
        infinite_threshold = np.where(~np.isfinite(tree.tree_.threshold))[0]
        assert len(infinite_threshold) == 0
        assert len(empty_leaf) == 0


@pytest.mark.parametrize("criterion", CLF_CRITERIONS)
@pytest.mark.parametrize(
    "dataset", sorted(set(DATASETS.keys()) - {"reg_small", "diabetes"}))
@pytest.mark.parametrize(
    "tree_cls", [DecisionTreeClassifier, ExtraTreeClassifier])
def test_prune_tree_classifier_are_subtrees(criterion, dataset, tree_cls):
    dataset = DATASETS[dataset]
    X, y = dataset["X"], dataset["y"]
    est = tree_cls(max_leaf_nodes=20, random_state=0)
    info = est.cost_complexity_pruning_path(X, y)

    pruning_path = info.ccp_alphas
    impurities = info.impurities
    assert np.all(np.diff(pruning_path) >= 0)
    assert np.all(np.diff(impurities) >= 0)

    assert_pruning_creates_subtree(tree_cls, X, y, pruning_path)


@pytest.mark.parametrize("criterion", REG_CRITERIONS)
@pytest.mark.parametrize("dataset", DATASETS.keys())
@pytest.mark.parametrize(
    "tree_cls", [DecisionTreeRegressor, ExtraTreeRegressor])
def test_prune_tree_regression_are_subtrees(criterion, dataset, tree_cls):
    dataset = DATASETS[dataset]
    X, y = dataset["X"], dataset["y"]

    est = tree_cls(max_leaf_nodes=20, random_state=0)
    info = est.cost_complexity_pruning_path(X, y)

    pruning_path = info.ccp_alphas
    impurities = info.impurities
    assert np.all(np.diff(pruning_path) >= 0)
    assert np.all(np.diff(impurities) >= 0)

    assert_pruning_creates_subtree(tree_cls, X, y, pruning_path)


def test_prune_single_node_tree():
    # single node tree
    clf1 = DecisionTreeClassifier(random_state=0)
    clf1.fit([[0], [1]], [0, 0])

    # pruned single node tree
    clf2 = DecisionTreeClassifier(random_state=0, ccp_alpha=10)
    clf2.fit([[0], [1]], [0, 0])

    assert_is_subtree(clf1.tree_, clf2.tree_)


def assert_pruning_creates_subtree(estimator_cls, X, y, pruning_path):
    # generate trees with increasing alphas
    estimators = []
    for ccp_alpha in pruning_path:
        est = estimator_cls(
            max_leaf_nodes=20, ccp_alpha=ccp_alpha, random_state=0).fit(X, y)
        estimators.append(est)

    # A pruned tree must be a subtree of the previous tree (which had a
    # smaller ccp_alpha)
    for prev_est, next_est in zip(estimators, estimators[1:]):
        assert_is_subtree(prev_est.tree_, next_est.tree_)


def assert_is_subtree(tree, subtree):
    assert tree.node_count >= subtree.node_count
    assert tree.max_depth >= subtree.max_depth

    tree_c_left = tree.children_left
    tree_c_right = tree.children_right
    subtree_c_left = subtree.children_left
    subtree_c_right = subtree.children_right

    stack = [(0, 0)]
    while stack:
        tree_node_idx, subtree_node_idx = stack.pop()
        assert_array_almost_equal(tree.value[tree_node_idx],
                                  subtree.value[subtree_node_idx])
        assert_almost_equal(tree.impurity[tree_node_idx],
                            subtree.impurity[subtree_node_idx])
        assert_almost_equal(tree.n_node_samples[tree_node_idx],
                            subtree.n_node_samples[subtree_node_idx])
        assert_almost_equal(tree.weighted_n_node_samples[tree_node_idx],
                            subtree.weighted_n_node_samples[subtree_node_idx])

        if (subtree_c_left[subtree_node_idx] ==
                subtree_c_right[subtree_node_idx]):
            # is a leaf
            assert_almost_equal(TREE_UNDEFINED,
                                subtree.threshold[subtree_node_idx])
        else:
            # not a leaf
            assert_almost_equal(tree.threshold[tree_node_idx],
                                subtree.threshold[subtree_node_idx])
            stack.append((tree_c_left[tree_node_idx],
                          subtree_c_left[subtree_node_idx]))
            stack.append((tree_c_right[tree_node_idx],
                          subtree_c_right[subtree_node_idx]))


def test_prune_tree_raises_negative_ccp_alpha():
    clf = DecisionTreeClassifier()
    msg = "ccp_alpha must be greater than or equal to 0"

    with pytest.raises(ValueError, match=msg):
        clf.set_params(ccp_alpha=-1.0)
        clf.fit(X, y)

    clf.set_params(ccp_alpha=0.0)
    clf.fit(X, y)

    with pytest.raises(ValueError, match=msg):
        clf.set_params(ccp_alpha=-1.0)
        clf._prune_tree()


def check_apply_path_readonly(name):
    X_readonly = create_memmap_backed_data(X_small.astype(tree._tree.DTYPE,
                                                          copy=False))
    y_readonly = create_memmap_backed_data(np.array(y_small,
                                                    dtype=tree._tree.DTYPE))
    est = ALL_TREES[name]()
    est.fit(X_readonly, y_readonly)
    assert_array_equal(est.predict(X_readonly),
                       est.predict(X_small))
    assert_array_equal(est.decision_path(X_readonly).todense(),
                       est.decision_path(X_small).todense())


@pytest.mark.parametrize("name", ALL_TREES)
def test_apply_path_readonly_all_trees(name):
    check_apply_path_readonly(name)


@pytest.mark.parametrize("criterion", ["mse", "friedman_mse", "poisson"])
@pytest.mark.parametrize("Tree", REG_TREES.values())
def test_balance_property(criterion, Tree):
    # Test that sum(y_pred)=sum(y_true) on training set.
    # This works if the mean is predicted (should even be true for each leaf).
    # MAE predicts the median and is therefore excluded from this test.

    # Choose a training set with non-negative targets (for poisson)
    X, y = diabetes.data, diabetes.target
    reg = Tree(criterion=criterion)
    reg.fit(X, y)
    assert np.sum(reg.predict(X)) == pytest.approx(np.sum(y))


@pytest.mark.parametrize("seed", range(3))
def test_poisson_zero_nodes(seed):
    # Test that sum(y)=0 and therefore y_pred=0 is forbidden on nodes.
    X = [[0, 0], [0, 1], [0, 2], [0, 3],
         [1, 0], [1, 2], [1, 2], [1, 3]]
    y = [0, 0, 0, 0, 1, 2, 3, 4]
    # Note that X[:, 0] == 0 is a 100% indicator for y == 0. The tree can
    # easily learn that:
    reg = DecisionTreeRegressor(criterion="mse", random_state=seed)
    reg.fit(X, y)
    assert np.amin(reg.predict(X)) == 0
    # whereas Poisson must predict strictly positive numbers
    reg = DecisionTreeRegressor(criterion="poisson", random_state=seed)
    reg.fit(X, y)
    assert np.all(reg.predict(X) > 0)

    # Test additional dataset where something could go wrong.
    n_features = 10
    X, y = datasets.make_regression(
        effective_rank=n_features * 2 // 3, tail_strength=0.6,
        n_samples=1_000,
        n_features=n_features,
        n_informative=n_features * 2 // 3,
        random_state=seed,
    )
    # some excess zeros
    y[(-1 < y) & (y < 0)] = 0
    # make sure the target is positive
    y = np.abs(y)
    reg = DecisionTreeRegressor(criterion='poisson', random_state=seed)
    reg.fit(X, y)
    assert np.all(reg.predict(X) > 0)


def test_poisson_vs_mse():
    # For a Poisson distributed target, Poisson loss should give better results
    # than least squares measured in Poisson deviance as metric.
    # We have a similar test, test_poisson(), in
    # sklearn/ensemble/_hist_gradient_boosting/tests/test_gradient_boosting.py
    # Note: Some fine tuning was needed to have metric_poi < metric_dummy on
    # the test set!
    rng = np.random.RandomState(42)
    n_train, n_test, n_features = 500, 500, 10
    X = datasets.make_low_rank_matrix(n_samples=n_train + n_test,
                                      n_features=n_features, random_state=rng)
    # We create a log-linear Poisson model and downscale coef as it will get
    # exponentiated.
    coef = rng.uniform(low=-2, high=2, size=n_features) / np.max(X, axis=0)
    y = rng.poisson(lam=np.exp(X @ coef))
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=n_test,
                                                        random_state=rng)
    # We prevent some overfitting by setting min_samples_split=10.
    tree_poi = DecisionTreeRegressor(criterion="poisson",
                                     min_samples_split=10,
                                     random_state=rng)
    tree_mse = DecisionTreeRegressor(criterion="mse",
                                     min_samples_split=10,
                                     random_state=rng)

    tree_poi.fit(X_train, y_train)
    tree_mse.fit(X_train, y_train)
    dummy = DummyRegressor(strategy="mean").fit(X_train, y_train)

    for X, y, val in [(X_train, y_train, "train"), (X_test, y_test, "test")]:
        metric_poi = mean_poisson_deviance(y, tree_poi.predict(X))
        # mse might produce non-positive predictions => clip
        metric_mse = mean_poisson_deviance(y, np.clip(tree_mse.predict(X),
                                                      1e-15, None))
        metric_dummy = mean_poisson_deviance(y, dummy.predict(X))
        # As MSE might correctly predict 0 in train set, its train score can
        # be better than Poisson. This is no longer the case for the test set.
        if val == "test":
            assert metric_poi < metric_mse
        assert metric_poi < metric_dummy


@pytest.mark.parametrize('criterion', REG_CRITERIONS)
def test_decision_tree_regressor_sample_weight_consistentcy(
        criterion):
    """Test that the impact of sample_weight is consistent."""
    tree_params = dict(criterion=criterion)
    tree = DecisionTreeRegressor(**tree_params, random_state=42)
    for kind in ['zeros', 'ones']:
        check_sample_weights_invariance("DecisionTreeRegressor_" + criterion,
                                        tree, kind='zeros')

    rng = np.random.RandomState(0)
    n_samples, n_features = 10, 5

    X = rng.rand(n_samples, n_features)
    y = np.mean(X, axis=1) + rng.rand(n_samples)
    # make it positive in order to work also for poisson criterion
    y += np.min(y) + 0.1

    # check that multiplying sample_weight by 2 is equivalent
    # to repeating corresponding samples twice
    X2 = np.concatenate([X, X[:n_samples//2]], axis=0)
    y2 = np.concatenate([y, y[:n_samples//2]])
    sample_weight_1 = np.ones(len(y))
    sample_weight_1[:n_samples//2] = 2

    tree1 = DecisionTreeRegressor(**tree_params).fit(
            X, y, sample_weight=sample_weight_1
    )

    tree2 = DecisionTreeRegressor(**tree_params).fit(
            X2, y2, sample_weight=None
    )

    assert tree1.tree_.node_count == tree2.tree_.node_count
    # Thresholds, tree.tree_.threshold, and values, tree.tree_.value, are not
    # exactly the same, but on the training set, those differences do not
    # matter and thus predictions are the same.
    assert_allclose(tree1.predict(X), tree2.predict(X))


# TODO: Remove in v0.26
@pytest.mark.parametrize("TreeEstimator", [DecisionTreeClassifier,
                                           DecisionTreeRegressor])
def test_X_idx_sorted_deprecated(TreeEstimator):
    X_idx_sorted = np.argsort(X, axis=0)

    tree = TreeEstimator()

    with pytest.warns(FutureWarning,
                      match="The parameter 'X_idx_sorted' is deprecated"):
        tree.fit(X, y, X_idx_sorted=X_idx_sorted)


def check_convert_tree_value_to_ndarray(Tree, tree_value_dtype):
    tree = Tree(random_state=0, store_tree_astype=tree_value_dtype)
    tree.fit(X, y)

    if tree_value_dtype is None:
        # Tree owns the value array memory
        # The .value property returns a view on the underlying array
        # Thus, we need to access the .base to test data ownership
        assert not tree.tree_.value.base.flags.owndata
    else:
        # Tree value array has be copied to separate NumPy array
        assert tree.tree_.value.dtype == tree_value_dtype
        assert tree.tree_.value.base.flags.owndata


@pytest.mark.parametrize('name, Tree', CLF_TREES.items())
@pytest.mark.parametrize('tree_value_dtype', CLF_TREE_VALUE_DTYPES)
def test_convert_tree_value_to_ndarray_clf(name, Tree, tree_value_dtype):
    check_convert_tree_value_to_ndarray(Tree, tree_value_dtype)


@pytest.mark.parametrize('name, Tree', REG_TREES.items())
@pytest.mark.parametrize('tree_value_dtype', REG_TREE_VALUE_DTYPES)
def test_convert_tree_value_to_ndarray_reg(name, Tree, tree_value_dtype):
    check_convert_tree_value_to_ndarray(Tree, tree_value_dtype)


@pytest.mark.parametrize('name, Tree', ALL_TREES.items())
@pytest.mark.parametrize('tree_value_dtype', REG_TREE_VALUE_DTYPES)
def test_pickle(name, Tree, tree_value_dtype):
    tree = Tree(random_state=0, store_tree_astype=tree_value_dtype)
    tree.fit(X, y)
    score = tree.score(X, y)
    pickle_object = pickle.dumps(tree)

    tree2 = pickle.loads(pickle_object)
    assert type(tree2) == tree.__class__
    assert tree.tree_.value.dtype == tree2.tree_.value.dtype
    # The .value property returns a view on the underlying array
    # Thus, we need to access the .base to test data ownership
    assert (tree.tree_.value.base.flags.owndata ==
            tree2.tree_.value.base.flags.owndata)
    score2 = tree2.score(X, y)
    assert score == score2


@pytest.mark.parametrize('name, Tree', ALL_TREES.items())
def test_tree_convert_value_to_ndarray(name, Tree):
    tree = Tree(random_state=0, store_tree_astype=None)
    tree.fit(X, y)

    # Error on invalid dtype
    with pytest.raises(TypeError):
        tree.tree_.convert_value_to_ndarray('failure')

    # Correct conversion
    if name in REG_TREES:
        tree.tree_.convert_value_to_ndarray('float32', strict=True)
        assert tree.tree_.value.dtype == np.float32
        tree.tree_.convert_value_to_ndarray('float32', strict=False)
        assert tree.tree_.value.dtype == np.float32

    if name in CLF_TREES:
        tree.tree_.convert_value_to_ndarray('uint8')
        assert tree.tree_.value.dtype == np.uint8
        tree.tree_.convert_value_to_ndarray('uint8', strict=False)
        assert tree.tree_.value.dtype == np.uint8
