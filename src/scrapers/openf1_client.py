import requests
from typing import List, Dict, Optional
from datetime import datetime


class OpenF1Client:
    def __init__(self):
        self.base_url = "https://api.openf1.org/v1"

    def get_sessions(self, year: int = 2024) -> List[Dict]:  # Use 2024 instead of 2025
        """Get F1 sessions data"""
        try:
            url = f"{self.base_url}/sessions"
            params = {'year': year}

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()

            sessions = response.json()
            print(f"📡 Retrieved {len(sessions)} sessions from OpenF1")

            return sessions
        except Exception as e:
            print(f"❌ Error fetching OpenF1 sessions: {e}")
            return []

    def get_drivers(self, session_key: Optional[int] = None) -> List[Dict]:
        """Get drivers data"""
        try:
            url = f"{self.base_url}/drivers"
            params = {}
            if session_key:
                params['session_key'] = session_key

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            drivers = response.json()
            print(f"📡 Retrieved {len(drivers)} drivers from OpenF1")

            return drivers
        except Exception as e:
            print(f"❌ Error fetching OpenF1 drivers: {e}")
            return []

    def get_lap_times(self, session_key: int, limit: int = 100) -> List[Dict]:
        """Get lap times data"""
        try:
            url = f"{self.base_url}/laps"
            params = {
                'session_key': session_key,
                'limit': limit
            }

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            laps = response.json()
            print(f"📡 Retrieved {len(laps)} lap times from OpenF1")

            return laps
        except Exception as e:
            print(f"❌ Error fetching OpenF1 lap times: {e}")
            return []

    def get_race_results(self, session_key: int) -> List[Dict]:
        """Get race results"""
        try:
            url = f"{self.base_url}/results"
            params = {'session_key': session_key}

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            results = response.json()
            print(f"📡 Retrieved {len(results)} results from OpenF1")

            return results
        except Exception as e:
            print(f"❌ Error fetching OpenF1 results: {e}")
            return []

    def get_meetings(self, year: int = 2025) -> List[Dict]:
        """Get F1 meetings/race weekends"""
        try:
            url = f"{self.base_url}/meetings"
            params = {'year': year}

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            meetings = response.json()
            print(f"📡 Retrieved {len(meetings)} meetings from OpenF1")

            return meetings
        except Exception as e:
            print(f"❌ Error fetching OpenF1 meetings: {e}")
            return []

    def get_positions(self, session_key: int) -> List[Dict]:
        """Get position data for a session"""
        try:
            url = f"{self.base_url}/position"
            params = {'session_key': session_key}

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            positions = response.json()
            print(f"📡 Retrieved position data from OpenF1")

            return positions
        except Exception as e:
            print(f"❌ Error fetching OpenF1 positions: {e}")
            return []

    def get_comprehensive_f1_data(self) -> Dict:
        """Get comprehensive F1 data from OpenF1 API"""
        try:
            print("📡 Fetching comprehensive F1 data from OpenF1...")

            # Get current year data
            current_year = 2025
            sessions = self.get_sessions(current_year)
            drivers = self.get_drivers()
            meetings = self.get_meetings(current_year)

            # Get latest race results
            race_results = []
            if sessions:
                # Filter for race sessions only
                race_sessions = [s for s in sessions if s.get('session_type') == 'Race']
                latest_races = sorted(race_sessions, key=lambda x: x.get('date_start', ''), reverse=True)[:5]

                for race_session in latest_races:
                    session_key = race_session.get('session_key')
                    if session_key:
                        results = self.get_race_results(session_key)
                        if results:
                            race_results.extend(results)

            return {
                'sessions': sessions,
                'drivers': drivers,
                'meetings': meetings,
                'race_results': race_results,
                'source': 'OpenF1 API',
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"❌ Error in OpenF1 comprehensive data fetch: {e}")
            return {}

    def format_for_rag(self, openf1_data: Dict) -> List[Dict]:
        """Format OpenF1 data for RAG ingestion"""
        formatted_documents = []

        try:
            # Process drivers data
            if openf1_data.get('drivers'):
                drivers_content = "Formula 1 Drivers 2025:\n"
                for driver in openf1_data['drivers']:
                    full_name = driver.get('full_name', 'Unknown Driver')
                    team = driver.get('team_name', 'Unknown Team')
                    number = driver.get('driver_number', 'N/A')
                    country = driver.get('country_code', 'Unknown')

                    drivers_content += f"• {full_name} (#{number}) - {team} - {country}\n"

                formatted_documents.append({
                    'title': 'Current F1 Drivers 2025',
                    'content': drivers_content,
                    'url': 'https://api.openf1.org/v1/drivers',
                    'source': 'OpenF1 API',
                    'type': 'driver_data',
                    'language': 'en'
                })

            # Process race results
            if openf1_data.get('race_results'):
                results_by_race = {}

                for result in openf1_data['race_results']:
                    session_key = result.get('session_key')
                    if session_key not in results_by_race:
                        results_by_race[session_key] = []
                    results_by_race[session_key].append(result)

                for session_key, results in results_by_race.items():
                    if results:
                        first_result = results[0]
                        race_name = f"Race Session {session_key}"

                        results_content = f"Race Results for {race_name}:\n"

                        # Sort by position
                        sorted_results = sorted(results, key=lambda x: x.get('position', 999))

                        for result in sorted_results[:10]:  # Top 10
                            position = result.get('position', 'N/A')
                            driver_number = result.get('driver_number', 'N/A')
                            points = result.get('points', 0)

                            results_content += f"{position}. Driver #{driver_number} - {points} points\n"

                        formatted_documents.append({
                            'title': f'F1 Race Results - Session {session_key}',
                            'content': results_content,
                            'url': f'https://api.openf1.org/v1/results?session_key={session_key}',
                            'source': 'OpenF1 API',
                            'type': 'race_results',
                            'language': 'en'
                        })

            # Process meetings/race calendar
            if openf1_data.get('meetings'):
                calendar_content = "Formula 1 2025 Race Calendar:\n"

                for meeting in openf1_data['meetings']:
                    meeting_name = meeting.get('meeting_name', 'Unknown Race')
                    location = meeting.get('location', 'Unknown Location')
                    country = meeting.get('country_name', 'Unknown Country')
                    date = meeting.get('date_start', 'TBD')

                    calendar_content += f"• {meeting_name} - {location}, {country} ({date})\n"

                formatted_documents.append({
                    'title': 'Formula 1 2025 Race Calendar',
                    'content': calendar_content,
                    'url': 'https://api.openf1.org/v1/meetings',
                    'source': 'OpenF1 API',
                    'type': 'race_calendar',
                    'language': 'en'
                })

            print(f"✅ Formatted {len(formatted_documents)} documents from OpenF1 data")
            return formatted_documents

        except Exception as e:
            print(f"❌ Error formatting OpenF1 data for RAG: {e}")
            return []
