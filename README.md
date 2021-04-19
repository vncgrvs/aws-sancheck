
<!-- [![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url] -->



<!-- PROJECT LOGO -->

<p align="center">
  <!-- <a href="https://github.com/othneildrew/Best-README-Template">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
  </a> -->

  <h2 align="center">LeanIX AWS Scan Healthchecker</h2>

  <p align="center">
    //
    <!-- <br />
    <a href="https://github.com/othneildrew/Best-README-Template"><strong>Explore the docs »</strong></a>
    <br /> -->
    <br />
    <a href="https://github.com/vg-leanix/aws_sancheck/issues">Report Bug</a>
    ·
    <a href="https://github.com/vg-leanix/aws_sancheck/issues">Request Feature</a>
  </p>
</p>



<!-- TABLE OF CONTENTS -->
<details open="open">
  <summary>Table of Contents</summary>
  <ol>
    <li><a href="#built-with">Built With</a></li>
    <li>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#examples">Examples</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgements">Acknowledgements</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

[![Product Name Screen Shot][product-screenshot]](https://www.leanix.net/en/)

This is a Python CLI to prepare the scan for [LeanIX Cloud Intelligence](https://dev.leanix.net/docs/cloud-intelligence). The CLI allows to check a given IAM role against all requirements and if successfull already populates the minimum-viable scan config in the scan config in the admin setting of the LeanIX CI Workspace. It also reads all activated cost-allocation tags.

### Built With


* [Python](https://www.python.org/)



<!-- GETTING STARTED -->
### Prerequisites

* Python >3.0


### Installation

1. create a virtual environment *e.g. venv*  
  
  ``` python
  python3 -m venv aws_scanner
  ```
2. activate the virtual environment
``` bash 
source aws_scanner/bin/activate
  ```
3.  install the package
  ``` python
  pip install haws
  ```


<!-- USAGE EXAMPLES -->
## Usage

### setup
```haws setup``` will guide you through setting up the needed data (i.e. credentials and other config) to run ```haws run``` later on.

### run 
```haws run``` is the core of the CLI. It runs the credential-,policy-, organizational layout- and cost allocation-tag check

**Options:**
1. ```--save-runtime```: **[boolean]** if set, will store the config set under ```haws setup``` after the checks are done.<br/>Default: **False**
2. ```--write-config```: **[boolean]** if set, will overwrite the LeanIX Cloud Scan config in the specified workspace.<br/>Default: **False**
3. ```--get-org```: **[boolean]** if set, will traverse the AWS Organization and create a org chart.<br/>Default: **False**

## Examples

### Setting up the scanner
  ```
  haws setup
  ```

### Running the healthchecks
  ```
  haws run
  ```

### Running the healthchecks and saving the runtime config
  ```
  haws run --save-runtime
  ```



<!-- LICENSE -->
## License

Distributed under the Apache 2.0 License. See `LICENSE` for more information.



<!-- CONTACT -->
## Contact

Vincent Groves - vincent.groves@leanix.nex





<!-- ACKNOWLEDGEMENTS -->
## Acknowledgements







<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/othneildrew/Best-README-Template.svg?style=for-the-badge
[contributors-url]: https://github.com/othneildrew/Best-README-Template/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/othneildrew/Best-README-Template.svg?style=for-the-badge
[forks-url]: https://github.com/othneildrew/Best-README-Template/network/members
[stars-shield]: https://img.shields.io/github/stars/othneildrew/Best-README-Template.svg?style=for-the-badge
[stars-url]: https://github.com/othneildrew/Best-README-Template/stargazers
[issues-shield]: https://img.shields.io/github/issues/othneildrew/Best-README-Template.svg?style=for-the-badge
[issues-url]: https://github.com/othneildrew/Best-README-Template/issues
[license-shield]: https://img.shields.io/github/license/othneildrew/Best-README-Template.svg?style=for-the-badge
[license-url]: https://github.com/othneildrew/Best-README-Template/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://www.linkedin.com/in/vincegroves/
[product-screenshot]: thumbnail.png
