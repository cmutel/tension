from .brightway_utils import get_dataframe
from .balancing import get_report_for_code
from flask import (
    Flask,
    render_template,
)
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent

tension_app = Flask(
    "tension_app",
    static_folder=os.fspath(BASE_DIR / "assets"),
    template_folder=os.fspath(BASE_DIR / "assets" / "templates")
)


df = get_dataframe()

by_isic = df.groupby('isic').mean().sort_values('difference')
by_isic['isic'] = by_isic.index
by_isic.sort_values('difference', inplace=True)
cols = [by_isic.columns[-1]] + [col for col in by_isic if col != by_isic.columns[-1]]
by_isic = by_isic[cols]


@tension_app.route("/", methods=["GET"])
def index():
    return render_template("index.html", data=by_isic.to_json(orient="records"), title="Tension index page")


@tension_app.route("/isic/<code>", methods=["GET"])
def isic(code):
    fdf = df[df['isic'] == code].sort_values('difference')
    fdf['url'] = "/activity/" + df['code']
    return render_template("isic.html", code=code, data=fdf.to_json(orient="records"), title="ISIC detail page")


@tension_app.route("/activity/<code>", methods=["GET"])
def activity(code):
    act, df = get_report_for_code(code)

    inputs = [row for row in df if row['sign'] < 0]
    outputs = [row for row in df if row['sign'] > 0]

    print(inputs)

    return render_template("activity.html", act=act, inputdata=inputs, outputdata=outputs, title="Activity detail page")
