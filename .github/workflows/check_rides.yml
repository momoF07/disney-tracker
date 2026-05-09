name: 🎢 Check Rides Names

on:
  workflow_dispatch:

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - name: 🐍 Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: 📦 Install
        run: pip install requests

      - name: 🎢 List Rides
        run: |
          python -c "
          import requests
          PARKS = ['dae968d5-630d-4719-8b06-3d107e944401', 'ca888437-ebb4-4d50-aed2-d227f7096968']
          for p_id in PARKS:
              res = requests.get(f'https://api.themeparks.wiki/v1/entity/{p_id}/live', timeout=15)
              data = res.json().get('liveData', [])
              print(f'\n=== {p_id} ===')
              for item in data:
                  if item.get('entityType') == 'ATTRACTION':
                      print(f'  {item.get(\"name\")}')
          "
