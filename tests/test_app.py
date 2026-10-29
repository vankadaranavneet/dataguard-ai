from pathlib import Path
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / 'app.py'


def test_demo_dashboard():
    app = AppTest.from_file(str(APP)).run(timeout=30)
    assert not app.exception
    assert [m.value for m in app.metric] == ['84.32/100', '10', '7', '14']
    assert len(app.get('plotly_chart')) == 3
    assert len(app.get('download_button')) == 2
    app.multiselect[0].set_value(['High']).run()
    assert not app.exception
    app.text_area[0].set_value('{"absent":{"required":true}}').run()
    assert 'missing' in app.error[0].value
    assert not app.exception


def test_upload_waiting_state_and_invalid_json():
    app = AppTest.from_file(str(APP)).run(timeout=30)
    app.text_area[0].set_value('{bad').run()
    assert app.error and not app.exception
    app.radio[0].set_value('Upload CSV').run()
    assert app.info and not app.exception
