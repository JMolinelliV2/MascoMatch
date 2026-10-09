import importlib.util
from pathlib import Path
import pytest


def initializer():
    path=next((parent/"tools"/"production_init.py" for parent in Path(__file__).resolve().parents if (parent/"tools"/"production_init.py").is_file()),None)
    if path is None:
        pytest.skip("Operator tooling is tested from the repository root")
    spec=importlib.util.spec_from_file_location("production_init",path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.initialize


def test_private_deployment_generation_does_not_replace_keys(tmp_path):
    initialize=initializer()
    initialize(tmp_path)
    before=(tmp_path/".secrets"/"jwt_secret").read_text()
    assert len(before.strip())>=48
    assert "MAIL_DELIVERY_MODE=disabled" in (tmp_path/".env.production").read_text()
    assert before.strip() not in (tmp_path/".env.production").read_text()
    with pytest.raises(FileExistsError):initialize(tmp_path)
    assert (tmp_path/".secrets"/"jwt_secret").read_text()==before


def test_deployment_domain_cannot_inject_configuration(tmp_path):
    with pytest.raises(ValueError):initializer()(tmp_path,"mascomatch.com\nSMTP_PASSWORD=unexpected")
