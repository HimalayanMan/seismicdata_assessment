# Installation and GitHub Submission

## 1. Create the repository

Create an empty GitHub repository named, for example:

```text
seismicdata_assessment
```

Do not auto-create a README or `.gitignore`; this project already contains them.

## 2. From Google Colab

Upload the ZIP and extract it, or clone the repository after the first push.

For an initial push from Colab:

```python
!unzip -q /content/seismicdata_assessment_pro.zip -d /content/
%cd /content/seismicdata_assessment_pro
```

Then configure Git:

```bash
git init
git branch -M main
git config --global user.name "YOUR NAME"
git config --global user.email "YOUR EMAIL"
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/seismicdata_assessment.git
git add .
git status
git commit -m "Initial seismic data assessment implementation"
git push -u origin main
```

### Authentication

Use GitHub CLI or a GitHub Personal Access Token if GitHub asks for
authentication. Never hard-code credentials or tokens in source code.

## 3. Clone test

After pushing, verify that a clean clone works:

```python
!rm -rf /content/clean_test
!git clone https://github.com/YOUR_GITHUB_USERNAME/seismicdata_assessment.git /content/clean_test
%cd /content/clean_test
!pip install -r requirements.txt
```

Put the evaluator's files into:

```text
data/SEP/
```

Then:

```python
!python run_pipeline.py --data-dir data/SEP --output-dir output
```

## 4. Run the notebook

Open:

```text
notebooks/main.ipynb
```

Run cells top-to-bottom.

The notebook is intentionally lightweight; the real application logic is in
`src/seismicdata/` so the evaluator can inspect/test normal Python modules.

## 5. Git status before submission

```bash
git status
git log --oneline --max-count=5
```

Check that secrets and generated local databases are not committed.

## 6. Normal update cycle

```bash
git add .
git commit -m "Improve seismic data visualization"
git push
```

## 7. Data-file policy

The assignment states that evaluators already have:

- `SEP01.mseed`
- `SEP02.mseed`
- `SEP03.mseed`

Therefore `.gitignore` excludes `data/SEP/*.mseed`.

If the evaluator specifically requests that those files be committed, and
their redistribution is allowed, remove that `.gitignore` line and commit them.

## 8. Recommended repository submission

The GitHub repository should contain:

- source code
- SQL files
- notebook
- requirements
- tests
- README
- documentation
- `.gitignore`

It does not need generated SQLite/PNG/HTML files because those are reproducible
from the supplied data.
