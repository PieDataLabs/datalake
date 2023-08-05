#!/usr/bin/env bash

rm -rf package_data
mkdir package_data
cp -r ./datalake ./package_data/
cp -r ./scripts ./package_data
cp ./setup.py ./package_data/

cp ./MANIFEST.in ./package_data/
cp ./requirements.txt ./package_data/
cp ./README.md ./package_data/

cd package_data && python setup.py build_ext --inplace && python setup.py bdist_wheel
cp ./dist/*.whl ../
rm -rf ../package_data
