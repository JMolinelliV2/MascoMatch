from app.core.rate_limit import WindowLimiter


def test_basic_request_limits_are_scoped_and_expire():
    clock=[0]
    limiter=WindowLimiter(lambda:clock[0])
    assert limiter.allow(("auth","client-a"),2)[0]
    assert limiter.allow(("auth","client-a"),2)[0]
    assert limiter.allow(("auth","client-a"),2)==(False,60)
    assert limiter.allow(("auth","client-b"),2)[0]
    assert limiter.allow(("publish","client-a"),2)[0]
    clock[0]=61
    assert limiter.allow(("auth","client-a"),2)[0]
