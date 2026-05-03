import requests
from flask import Blueprint, render_template

api_bp = Blueprint('api', __name__)


def get_random_cat_image():
    try:
        response = requests.get('https://cataas.com/cat?json=true', timeout=10)

        if response.status_code == 200:
            data = response.json()
            cat_url = 'https://cataas.com' + data.get('url', '/cat')
            return cat_url
        else:
            return 'https://cataas.com/cat'

    except Exception as e:
        print(f"Ошибка API: {e}")
        return 'https://cataas.com/cat'


@api_bp.route('/random-cat')
def random_cat():
    cat_image_url = get_random_cat_image()
    return render_template('cat_api.html', cat_image_url=cat_image_url)
