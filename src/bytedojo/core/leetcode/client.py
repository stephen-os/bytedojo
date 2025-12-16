"""LeetCode API client."""

import requests
import click
from typing import Optional
from bytedojo.core.logger import get_logger
from bytedojo.core.leetcode.models import Problem, CodeSnippet


class LeetCodeClient:
    """LeetCode API client - handles only API interactions."""
    
    GRAPHQL_URL: str = "https://leetcode.com/graphql"
    PROBLEMSET_URL: str = "https://leetcode.com/api/problems/all/"
    
    QUERY: str = """
    query questionData($titleSlug: String!) {
        question(titleSlug: $titleSlug) {
            questionId
            title
            titleSlug
            difficulty
            content
            exampleTestcases
            codeSnippets {
                lang
                code
            }
        }
    }
    """
    
    def __init__(self) -> None:
        """Initialize the client with a requests session."""
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        })
        self.logger = get_logger()
    
    def get_problem_by_id(self, problem_id: int) -> Optional[Problem]:
        """
        Fetch problem details by problem ID (number).
        
        Args:
            problem_id: LeetCode problem number
            
        Returns:
            Problem object or None if not found
            
        Raises:
            click.ClickException: If fetching fails
        """
        if not problem_id:
            return None
        
        try:
            title_slug = self._get_title_slug_by_id(problem_id)
            if not title_slug:
                self.logger.debug(f"No title slug found for problem ID {problem_id}")
                return None
            
            self.logger.debug(f"Problem {problem_id} -> slug: {title_slug}")
            return self._fetch_problem(title_slug)
            
        except requests.RequestException as e:
            self.logger.error(f"Network error fetching problem {problem_id}: {e}")
            raise click.ClickException(f"Failed to fetch problem {problem_id}: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error fetching problem {problem_id}: {e}")
            raise click.ClickException(f"Unexpected error: {e}")
    
    def get_problem_by_name(self, problem_name: str) -> Optional[Problem]:
        """
        Fetch problem details by problem name/title slug.
        
        Args:
            problem_name: Problem name (e.g., "two sum")
            
        Returns:
            Problem object or None if not found
            
        Raises:
            click.ClickException: If fetching fails
        """
        if not problem_name:
            return None
        
        try:
            # Convert name to slug format
            title_slug = problem_name.lower().replace(' ', '-')
            self.logger.debug(f"Searching for problem: '{problem_name}' -> slug: '{title_slug}'")
            return self._fetch_problem(title_slug)
            
        except requests.RequestException as e:
            self.logger.error(f"Network error fetching problem '{problem_name}': {e}")
            raise click.ClickException(f"Failed to fetch problem '{problem_name}': {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error fetching problem '{problem_name}': {e}")
            raise click.ClickException(f"Unexpected error: {e}")
    
    def _fetch_problem(self, title_slug: str) -> Optional[Problem]:
        """
        Fetch problem and return as Problem object.
        
        Args:
            title_slug: Problem title slug (e.g., "two-sum")
            
        Returns:
            Problem object or None if not found
        """
        data = self._fetch_raw_data(title_slug)
        if not data:
            return None
        
        # Parse into Problem dataclass
        return Problem(
            id=int(data['questionId']),
            title=data['title'],
            title_slug=data['titleSlug'],
            difficulty=data['difficulty'],
            description=data['content'],
            test_cases=data.get('exampleTestcases', ''),
            code_snippets=[
                CodeSnippet(lang=s['lang'], code=s['code'])
                for s in data.get('codeSnippets', [])
            ]
        )
    
    def _fetch_raw_data(self, title_slug: str) -> Optional[dict]:
        """
        Fetch raw problem data from GraphQL API.
        
        Args:
            title_slug: Problem title slug
            
        Returns:
            Raw problem data dictionary or None
        """
        self.logger.debug(f"Fetching problem details for slug: {title_slug}")
        
        payload = {
            'query': self.QUERY,
            'variables': {'titleSlug': title_slug}
        }
        
        response = self.session.post(self.GRAPHQL_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        
        if 'data' in data and 'question' in data['data']:
            return data['data']['question']
        
        self.logger.warning(f"No problem data found for slug: {title_slug}")
        return None
    
    def _get_title_slug_by_id(self, problem_id: int) -> Optional[str]:
        """
        Get the title slug for a problem ID.
        
        Args:
            problem_id: LeetCode problem number
            
        Returns:
            Title slug string or None if not found
            
        Raises:
            requests.RequestException: If API request fails
        """
        self.logger.debug(f"Fetching problem list to find slug for ID {problem_id}")
        
        response = self.session.get(self.PROBLEMSET_URL)
        response.raise_for_status()
        data = response.json()
        
        if 'stat_status_pairs' not in data:
            self.logger.warning("Problem list response missing 'stat_status_pairs'")
            return None
        
        for problem in data['stat_status_pairs']:
            if problem['stat']['question_id'] == problem_id:
                return problem['stat']['question__title_slug']
        
        return None