Running local tests
^^^^^^^^^^^^^^^^^^^

The unit tests for drf-social-oauth2 are located in the tests/ directory. To run these tests on your local
machine, you will need to first build the Docker image and then execute the test run command. To do so,
follow these steps:

Build the Docker image by running the following command:

.. code-block:: console

    $ docker-compose -f docker-compose.tests.yml build --no-cache

Execute the test run command by running the following command:

.. code-block:: console

    $ docker-compose -f docker-compose.tests.yml up --exit-code-from app

Once the tests have completed, you can view the results in the htmlcov/ folder in your local environment.
The index.html file provides detailed information about the test coverage of the project.

To clean up your local system and remove all containers created during the testing process, run the following command:

.. code-block:: console

    $ docker-compose -f docker-compose.tests.yml down
