from pathlib import Path
import setuptools


readme = Path('README.md').read_text()
requirements = Path('requirements.txt').read_text().splitlines()

setuptools.setup(
        name='quartz',
        version='0.0.33',
        author='thisgary',
        author_email='gary.github@gmail.com',
        description='Sheets API & Discord API Automation',
        long_description=readme,
        long_description_content_type='text/markdown',
        packages=setuptools.find_packages(),
        classifiers=[
            'Programming Language :: Python :: 3',
            'License :: OSI Approved :: MIT Lisence',
            'Operating System :: OS Independent',
        ],
        license='MIT',
        python_requires='>=3.8',
        install_requires=requirements,
        setup_requires=['pytest_runner'],
        tests_require=['pytest'],
        test_suite='tests',
)

