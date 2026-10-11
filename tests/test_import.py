def test_clara_import():
    import clara
    from fastapi import FastAPI

    assert clara is not None
    assert isinstance(clara.app, FastAPI)
    assert isinstance(clara.clara, FastAPI)
    assert clara.app is clara.clara
