"""LeetCode API wrapper."""

import requests
from typing import Optional, List
from bytedojo.core.logger import get_logger
from bytedojo.core.models import Problem, CodeSnippet, ProblemSummary


class LeetCodeAPI:
    """LeetCode API - fetches problems and metadata."""
    
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
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error fetching problem {problem_id}: {e}")
            return None
    
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
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error fetching problem '{problem_name}': {e}")
            return None
    
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
        
        self.logger.debug(f"{data}")

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
                for s in (data.get('codeSnippets') or [])
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

    def query_problems(
        self,
        difficulty: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> List[ProblemSummary]:
        """
        Query LeetCode problems with optional filters.

        Args:
            difficulty: Filter by difficulty (1=Easy, 2=Medium, 3=Hard)
            tags: Filter by algorithm tags (e.g., ["array", "dynamic-programming"])

        Returns:
            List of ProblemSummary objects matching the filters, sorted by ID ascending

        Raises:
            click.ClickException: If query fails
        """
        try:
            # Get all problems with their tags
            problems_data = self._fetch_all_problems()
            if not problems_data:
                return []

            # Get tag mapping for problems
            tag_map = self._fetch_problem_tags()

            results = []
            difficulty_map = {1: 'Easy', 2: 'Medium', 3: 'Hard'}

            for problem in problems_data:
                stat = problem.get('stat', {})
                diff = problem.get('difficulty', {})

                problem_id = stat.get('question_id')
                problem_difficulty = diff.get('level')
                paid_only = problem.get('paid_only', False)

                # Apply difficulty filter
                if difficulty is not None and problem_difficulty != difficulty:
                    continue

                # Get tags for this problem
                problem_tags = tag_map.get(problem_id, [])

                # Apply tag filter (match any tag)
                if tags:
                    normalized_tags = [t.lower().replace(' ', '-') for t in tags]
                    problem_tag_slugs = [t.lower().replace(' ', '-') for t in problem_tags]
                    if not any(t in problem_tag_slugs for t in normalized_tags):
                        continue

                results.append(ProblemSummary(
                    id=problem_id,
                    title=stat.get('question__title', ''),
                    title_slug=stat.get('question__title_slug', ''),
                    difficulty=difficulty_map.get(problem_difficulty, 'Unknown'),
                    paid_only=paid_only,
                    tags=problem_tags
                ))

            # Sort by problem ID ascending
            results.sort(key=lambda p: p.id)

            return results

        except requests.RequestException as e:
            self.logger.error(f"Network error querying problems: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error querying problems: {e}")
            return []

    def _fetch_all_problems(self) -> Optional[List[dict]]:
        """
        Fetch all problems from the problemset API.

        Returns:
            List of problem data dictionaries or None
        """
        self.logger.debug("Fetching all problems from problemset API")

        response = self.session.get(self.PROBLEMSET_URL)
        response.raise_for_status()
        data = response.json()

        return data.get('stat_status_pairs', [])

    def _fetch_problem_tags(self) -> dict:
        """
        Fetch problem tags mapping from GraphQL API.

        Returns:
            Dictionary mapping problem IDs to lists of tag names
        """
        self.logger.debug("Fetching problem tags")

        query = """
        query problemsetQuestionList {
            problemsetQuestionList: questionList(
                categorySlug: ""
                limit: -1
                skip: 0
                filters: {}
            ) {
                questions: data {
                    questionFrontendId
                    topicTags {
                        name
                        slug
                    }
                }
            }
        }
        """

        payload = {'query': query}

        try:
            response = self.session.post(self.GRAPHQL_URL, json=payload)
            response.raise_for_status()
            data = response.json()

            tag_map = {}
            questions = data.get('data', {}).get('problemsetQuestionList', {}).get('questions', [])

            for q in questions:
                try:
                    problem_id = int(q.get('questionFrontendId', 0))
                    tags = [t.get('name', '') for t in q.get('topicTags', [])]
                    tag_map[problem_id] = tags
                except (ValueError, TypeError):
                    continue

            return tag_map

        except Exception as e:
            self.logger.warning(f"Failed to fetch problem tags: {e}")
            return {}

    def get_available_tags(self) -> List[str]:
        """
        Get list of all available algorithm tags.

        Returns:
            List of tag names
        """
        try:
            tag_map = self._fetch_problem_tags()
            all_tags = set()
            for tags in tag_map.values():
                all_tags.update(tags)
            return sorted(all_tags)
        except Exception as e:
            self.logger.warning(f"Failed to get available tags: {e}")
            return []