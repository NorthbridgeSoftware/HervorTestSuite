from argparse import ArgumentParser, ArgumentError
from termcolor import cprint
from dataclasses import dataclass
from requests import request
from json import load
from typing import Optional


@dataclass
class TestCase:
    """
    Represents a test to be applied
        to an API endpoint.
    """
    name: str  # Name of the test to be conducted.
    endpoint: str  # Endpoint URI.
    method: str  # Method to send the API call.
    status: int  # Status code expected from request.
    output: Optional[str]  # Expected output from the request.

    def conduct(self, base_uri: str) -> bool:
        """
        Conduct a test using the data about
            the test, as well as a base_uri.

        :param self: The object itself.
        :param base_uri: Base URI of the
            backend server.
        :return Whether or not the test is
            successful.
        """
        req = request(self.method, base_uri + self.endpoint)
        result = req.status_code == self.status
        if self.output is not None:
            result = result and (req.text == self.output)
        return result


@dataclass
class TestGroup:
    """
    Represents a group of tests that
        is tied by a common theme,
        useful for REST.
    """
    name: str  # Name of the group.
    test_cases: list[TestCase]  # A list of test cases.


@dataclass
class Test:
    """
    Represents an API Test bundle, all
        test cases bundled together, with
        related metadata.
    """
    name: str  # Program name.
    variables: dict[str, str]  # Variables to be used.
    default_uri: str  # The URI to be used if not overridden.
    test_groups: list[TestGroup]  # The list of test groups.


def parse_test_case(test_case_data: dict) -> TestCase:
    """
    Parse a test case from a given dictionary.

    :param test_case_data: A dictionary holding
        test case data.
    :return: A TestCase object parsed from a
        dictionary.
    """
    return TestCase(test_case_data['Name'],
                    test_case_data['Endpoint'],
                    test_case_data['Method'],
                    test_case_data['Status'],
                    test_case_data.get('Output'))


def parse_test_cases(test_group_data: list[dict]) -> list[TestCase]:
    """
    Parse test cases given in the test file as
        a list of dictionaries to a list of
        TestCase objects.

    :param test_group_data: The data about test
        cases within a test group as a list of
        dictionaries.
    :return A list of TestCase objects.
    """
    test_cases: list[TestCase] = []
    for test_case_data in test_group_data:
        test_cases.append(parse_test_case(test_case_data))
    return test_cases


def parse_test_groups(program_data: dict) -> list[TestGroup]:
    """
    Parse TestGroups in the test file.

    :param program_data: The Python object parsed
        from JSON file containing the program data.
    :return: The list of TestGroups inside the test.
    """
    if "Default URI" in program_data:
        del program_data["Default URI"]
    del program_data["Name"]
    test_groups = []
    for test_name in program_data:
        test_groups.append(
            TestGroup(test_name, parse_test_cases(program_data[test_name]))
        )
    return test_groups


def parse_tests(file_name: str) -> Test:
    """
    Parse a test file from a file name.
        The test file must be in JSON
        format.

    :param file_name: Name of the file containing
        the test data.
    :return: The Test class.
    """
    with open(file_name, "r") as file:
        program_data = load(file)
    default_uri = program_data.get('Default URI')
    return Test(program_data['Name'], {}, default_uri,
                parse_test_groups(program_data))


def conduct_tests(test: Test, base_uri: str) -> None:
    """
    Conduct all the tests and print their
        results.

    :param test: The Test object holding
        all the test cases.
    """
    if base_uri is None:
        if test.default_uri is None:
            raise ArgumentError("No base URI provided "
                                + "and no default URI.")
        base_uri = test.default_uri
    for test_group in test.test_groups:
        cprint(test_group.name, "blue")
        for test_case in test_group.test_cases:
            cprint(f"\t{test_case.name} Testing", "grey", end="")
            test_result = test_case.conduct(base_uri)
            if test_result:
                cprint(f"\r\t{test_case.name} Passed!", "green")
            else:
                cprint(f"\r\t{test_case.name} Failed!", "red")


if __name__ == '__main__':
    parser = ArgumentParser(prog="Hervor API Test Suite",
                            description="Hervor Test Suite can be"
                            + " used to automatically test API"
                            + "backends built on HTTP.")
    parser.add_argument("-t", "--test", required=True,
                        help="Test file written in JSON.")
    parser.add_argument("-b", "--base_uri", required=True,
                        help="Base URL of the backend.")
    args = parser.parse_args()
    conduct_tests(parse_tests(args.test), args.base_uri)
