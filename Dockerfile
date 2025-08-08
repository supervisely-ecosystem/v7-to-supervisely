FROM supervisely/base-py-sdk:6.73.418

RUN pip install darwin-py==0.8.48
RUN pip install --upgrade requests_toolbelt