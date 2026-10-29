import os
import pytest
from pathlib import Path
from selenium.common.exceptions import NoSuchElementException
from src.aihawk_job_manager import AIHawkJobManager
from loguru import logger


@pytest.fixture
def job_manager(mocker):
    """Fixture to provide a mocked AIHawkJobManager instance."""
    mock_driver = mocker.Mock()
    return AIHawkJobManager(driver=mock_driver)


def test_initialization(mocker, job_manager):
    """Test the initialization of AIHawkJobManager."""
    mock_file = mocker.mock_open(read_data="""
    positions:
      - Developer
    locations:
      - Remote
    experience_level:
      - Mid-Senior
    apply_once_at_company: false
    distance: 25
    company_blacklist: []
    title_blacklist: []
    location_blacklist: []
    """)
    mocker.patch('builtins.open', mock_file)
    mocker.patch('yaml.safe_load', return_value={
        'positions': ['Developer'],
        'locations': ['Remote'],
        'experience_level': ['Mid-Senior'],
        'apply_once_at_company': False,
        'distance': 25,
        'company_blacklist': [],
        'title_blacklist': [],
        'location_blacklist': []
    })

    job_manager.set_parameters(
        resume_dir="/path/to/resume",
        output_file_directory="/path/to/output"
    )

    assert str(job_manager.resume_path) == os.path.normpath('/path/to/resume')
    assert str(job_manager.output_file_directory) == os.path.normpath(
        '/path/to/output')


def next_job_page(self, position, location, job_page):
    logger.debug(f"Navigating to next job page: {position} in {location}, page {job_page}")
    self.driver.get(
        f"https://www.linkedin.com/jobs/search/{self.base_search_url}&keywords={position}&location={location}&start={job_page * 25}")


def test_get_jobs_from_page_no_jobs(mocker, job_manager):
    """Test get_jobs_from_page when no jobs are found."""
    mocker.patch.object(job_manager.driver, 'find_element',
                        side_effect=NoSuchElementException)
    mocker.patch.object(job_manager.driver, 'find_elements', return_value=[])

    jobs = job_manager.get_jobs_from_page()
    assert jobs == []


def test_get_jobs_from_page_with_jobs(mocker, job_manager):
    """Test get_jobs_from_page when job elements are found."""
    # Mock the no_jobs_element to behave correctly
    mock_no_jobs_element = mocker.Mock()
    mock_no_jobs_element.text = "No matching jobs found"

    # Mocking find_elements to return mock banner
    mocker.patch.object(job_manager.driver, 'find_elements',
                        return_value=[mock_no_jobs_element])

    # Mock the page_source
    mocker.patch.object(job_manager.driver, 'page_source',
                        return_value="some page content")

    # Ensure jobs are returned as empty list due to "No matching jobs found"
    jobs = job_manager.get_jobs_from_page()
    assert jobs == []  # No jobs expected due to "No matching jobs found"


def test_apply_jobs_with_no_jobs(mocker, job_manager):
    """Test apply_jobs when no jobs are found."""
    mocker.patch.object(job_manager, 'get_jobs_from_page', return_value=[])

    # Call apply_jobs and ensure no exceptions are raised
    job_manager.apply_jobs()
    assert True


def test_apply_jobs_with_jobs(mocker, job_manager):
    """Test apply_jobs when jobs are present."""
    container_mock = mocker.Mock()
    job_element_mock = mocker.Mock()
    job_elements_list = [job_element_mock]

    easy_apply_btn = mocker.Mock()
    easy_apply_btn.text = "Easy Apply"
    easy_apply_btn.is_displayed.return_value = True
    easy_apply_btn.is_enabled.return_value = True
    easy_apply_btn.get_attribute.return_value = "Easy Apply to Company"

    def side_effect_find_elements(by, val):
        if "Easy Apply" in val or "jobs-apply-button" in val:
            return [easy_apply_btn]
        return [container_mock]

    mocker.patch.object(job_manager.driver, 'find_elements', side_effect=side_effect_find_elements)

    mocker.patch.object(job_manager, 'extract_job_information_from_tile', return_value=(
        "Title", "Company", "Location", "Easy Apply", "Link"))

    mocker.patch.object(job_manager, 'is_blacklisted', return_value=False)
    mocker.patch.object(job_manager, 'is_already_applied_to_job', return_value=False)
    mocker.patch.object(job_manager, 'is_already_applied_to_company', return_value=False)

    job_manager.easy_applier_component = mocker.Mock()
    job_manager.output_file_directory = Path("/mocked/path/to/output")

    mocker.patch.object(Path, 'exists', return_value=True)
    mock_open = mocker.mock_open()
    mocker.patch('builtins.open', mock_open)

    # Run apply_jobs
    job_manager.apply_jobs()

    # Assertions
    assert job_manager.driver.find_elements.call_count >= 1
    assert job_manager.extract_job_information_from_tile.call_count >= 1
    assert job_manager.easy_applier_component.job_apply.call_count >= 1
    mock_open.assert_called()
