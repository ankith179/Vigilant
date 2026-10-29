import numpy as np

from scripts.run_contextual_bandit import LinUCB, fit_scaler, query_features, scale_feature


def test_context_features_and_scaler_are_finite():
    values = [query_features("reset password 123"), query_features("user login")]
    mean, scale = fit_scaler(values)
    encoded = scale_feature(values[0], mean, scale)
    assert encoded.shape == (4,)
    assert np.isfinite(encoded).all()
    assert (scale > 0).all()


def test_linucb_learns_from_observed_training_rewards_only():
    policy = LinUCB(("left", "right"), 2, alpha=0.5)
    contexts = [np.array([1.0, -1.0]), np.array([1.0, 1.0])]
    for _ in range(80):
        for x in contexts:
            arm = policy.choose(x, explore=True)
            reward = float((x[1] < 0 and arm == "left") or (x[1] > 0 and arm == "right"))
            policy.update(arm, x, reward)
    assert policy.choose(contexts[0]) == "left"
    assert policy.choose(contexts[1]) == "right"
