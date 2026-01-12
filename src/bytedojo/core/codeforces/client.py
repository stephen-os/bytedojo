"""Codeforces API client."""

import requests
import click
import re
from bs4 import BeautifulSoup
from typing import Optional, List
from bytedojo.core.logger import get_logger
from bytedojo.core.codeforces.models import Problem, ProblemSummary


class CodeforcesClient:
    """Codeforces API client - handles API interactions."""

    API_URL: str = "https://codeforces.com/api"
    PROBLEM_URL: str = "https://codeforces.com/problemset/problem"

    def __init__(self) -> None:
        """Initialize the client with a requests session."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        self.logger = get_logger()
        self._problems_cache = None

    def get_problem(self, contest_id: int, index: str) -> Optional[Problem]:
        """
        Fetch problem details by contest ID and index.

        Args:
            contest_id: Codeforces contest ID (e.g., 1, 4, 1850)
            index: Problem index (e.g., 'A', 'B', 'C')

        Returns:
            Problem object or None if not found
        """
        try:
            # First get basic info from API
            problems = self._fetch_all_problems()
            problem_info = None

            for p in problems:
                if p.get('contestId') == contest_id and p.get('index') == index.upper():
                    problem_info = p
                    break

            if not problem_info:
                self.logger.warning(f"Problem {contest_id}{index} not found")
                return None

            # Scrape full problem details from webpage
            return self._scrape_problem(contest_id, index.upper(), problem_info)

        except requests.RequestException as e:
            self.logger.error(f"Network error fetching problem {contest_id}{index}: {e}")
            raise click.ClickException(f"Failed to fetch problem: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error fetching problem {contest_id}{index}: {e}")
            raise click.ClickException(f"Unexpected error: {e}")

    def get_problem_by_id(self, problem_id: str) -> Optional[Problem]:
        """
        Fetch problem by combined ID (e.g., '1A', '4B', '1850A').

        Args:
            problem_id: Combined contest ID and index

        Returns:
            Problem object or None if not found
        """
        # Parse problem_id into contest_id and index
        match = re.match(r'^(\d+)([A-Za-z]\d?)$', problem_id)
        if not match:
            self.logger.warning(f"Invalid problem ID format: {problem_id}")
            return None

        contest_id = int(match.group(1))
        index = match.group(2).upper()

        return self.get_problem(contest_id, index)

    def query_problems(
        self,
        rating_min: Optional[int] = None,
        rating_max: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> List[ProblemSummary]:
        """
        Query Codeforces problems with optional filters.

        Args:
            rating_min: Minimum difficulty rating
            rating_max: Maximum difficulty rating
            tags: Filter by tags (e.g., ["dp", "graphs"])

        Returns:
            List of ProblemSummary objects matching the filters, sorted by ID
        """
        try:
            problems = self._fetch_all_problems()
            results = []

            for p in problems:
                rating = p.get('rating')
                problem_tags = [t.lower() for t in p.get('tags', [])]

                # Apply rating filter
                if rating_min is not None:
                    if rating is None or rating < rating_min:
                        continue

                if rating_max is not None:
                    if rating is None or rating > rating_max:
                        continue

                # Apply tag filter (match any tag)
                if tags:
                    normalized_tags = [t.lower().replace(' ', '-') for t in tags]
                    if not any(t in problem_tags for t in normalized_tags):
                        continue

                results.append(ProblemSummary(
                    contest_id=p.get('contestId', 0),
                    index=p.get('index', ''),
                    name=p.get('name', ''),
                    rating=rating,
                    tags=p.get('tags', [])
                ))

            # Sort by contest ID and index
            results.sort(key=lambda p: (p.contest_id, p.index))

            return results

        except requests.RequestException as e:
            self.logger.error(f"Network error querying problems: {e}")
            raise click.ClickException(f"Failed to query problems: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error querying problems: {e}")
            raise click.ClickException(f"Unexpected error: {e}")

    def get_available_tags(self) -> List[str]:
        """
        Get list of all available problem tags.

        Returns:
            List of tag names
        """
        try:
            problems = self._fetch_all_problems()
            all_tags = set()

            for p in problems:
                all_tags.update(p.get('tags', []))

            return sorted(all_tags)
        except Exception as e:
            self.logger.warning(f"Failed to get available tags: {e}")
            return []

    def _fetch_all_problems(self) -> List[dict]:
        """
        Fetch all problems from the API.

        Returns:
            List of problem data dictionaries
        """
        if self._problems_cache is not None:
            return self._problems_cache

        self.logger.debug("Fetching problems from Codeforces API")

        response = self.session.get(f"{self.API_URL}/problemset.problems")
        response.raise_for_status()
        data = response.json()

        if data.get('status') != 'OK':
            self.logger.warning("Codeforces API returned non-OK status")
            return []

        self._problems_cache = data.get('result', {}).get('problems', [])
        return self._problems_cache

    def _scrape_problem(self, contest_id: int, index: str, problem_info: dict) -> Problem:
        """
        Scrape full problem details from the webpage.

        Args:
            contest_id: Contest ID
            index: Problem index
            problem_info: Basic problem info from API

        Returns:
            Problem object with full details
        """
        url = f"{self.PROBLEM_URL}/{contest_id}/{index}"
        self.logger.debug(f"Scraping problem from {url}")

        response = self.session.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract problem statement
        problem_div = soup.find('div', class_='problem-statement')

        if not problem_div:
            # Return basic problem without scraped content
            return Problem(
                contest_id=contest_id,
                index=index,
                name=problem_info.get('name', ''),
                rating=problem_info.get('rating'),
                tags=problem_info.get('tags', []),
                time_limit="Unknown",
                memory_limit="Unknown",
                description="Could not fetch problem description.",
                input_spec="",
                output_spec="",
                sample_tests=[],
                note=""
            )

        # Extract time and memory limits
        time_limit = "Unknown"
        memory_limit = "Unknown"

        time_div = problem_div.find('div', class_='time-limit')
        if time_div:
            time_limit = time_div.get_text().replace('time limit per test', '').strip()

        memory_div = problem_div.find('div', class_='memory-limit')
        if memory_div:
            memory_limit = memory_div.get_text().replace('memory limit per test', '').strip()

        # Extract description (first div after header)
        description = ""
        desc_divs = problem_div.find_all('div', recursive=False)
        for div in desc_divs:
            if not div.get('class'):
                description = str(div)
                break

        # Extract input specification
        input_spec = ""
        input_div = problem_div.find('div', class_='input-specification')
        if input_div:
            input_spec = str(input_div)

        # Extract output specification
        output_spec = ""
        output_div = problem_div.find('div', class_='output-specification')
        if output_div:
            output_spec = str(output_div)

        # Extract sample tests
        sample_tests = []
        sample_div = problem_div.find('div', class_='sample-test')
        if sample_div:
            inputs = sample_div.find_all('div', class_='input')
            outputs = sample_div.find_all('div', class_='output')

            for inp, out in zip(inputs, outputs):
                inp_pre = inp.find('pre')
                out_pre = out.find('pre')

                if inp_pre and out_pre:
                    # Handle <br> tags in pre elements
                    input_text = self._extract_pre_text(inp_pre)
                    output_text = self._extract_pre_text(out_pre)

                    sample_tests.append({
                        'input': input_text,
                        'output': output_text
                    })

        # Extract note
        note = ""
        note_div = problem_div.find('div', class_='note')
        if note_div:
            note = str(note_div)

        return Problem(
            contest_id=contest_id,
            index=index,
            name=problem_info.get('name', ''),
            rating=problem_info.get('rating'),
            tags=problem_info.get('tags', []),
            time_limit=time_limit,
            memory_limit=memory_limit,
            description=description,
            input_spec=input_spec,
            output_spec=output_spec,
            sample_tests=sample_tests,
            note=note
        )

    def _extract_pre_text(self, pre_element) -> str:
        """Extract text from pre element, handling <br> tags."""
        # Replace <br> with newlines
        for br in pre_element.find_all('br'):
            br.replace_with('\n')

        # Get text and clean up
        text = pre_element.get_text()
        # Remove leading/trailing whitespace but preserve internal newlines
        lines = text.split('\n')
        lines = [line.strip() for line in lines]
        return '\n'.join(lines).strip()
