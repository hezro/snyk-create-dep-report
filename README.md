# What is this script for? <br>

This script will generate a CSV of direct or transitive dependencies for each Snyk Organization<br>
You can also filter on whether or not the dependency is deprecated.

## Prerequisites:
- Python 3.9+
- Snyk Token
- Chrome

## Installation instructions:

Clone this repo and run <pre><code>pip3 install -r requirements.txt</pre></code><br>

## How do I use this script?<br>
#### By defaul the script will generate CSV reports for direct dependencies.
```shell
python3 ./snyk-create-dep-report.py
```
#### Script Options:
If you want generate a report for transitive dependencies then change the isTransitive string value to "true":<br>
By default this is set to "false".
```python
isTransitive = "true"
```
If you want to filter on isDeprecated then set the useDeprecatedFilter to True:<br>
By default this is set to False.
```python
 useDeprecatedFilter = True
```
After that set the isDeprecated string value to either "true" or "false".<br>
By default it is set to "false".
```python
useDeprecatedFilter = True
isDeprecated = "true"
```

### *** This script will open a Chrome window and direct you to login Snyk ***

## CSV Example:
![image](https://github.com/hezro/snyk-create-dep-report/assets/17459977/686aeb28-9d4d-4a81-bf13-f91b2efe137b)
