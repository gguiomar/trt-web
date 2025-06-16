import random
from .config import debug_log

class VSTtask:
    def __init__(self, n_quadrants: int = 4, n_queues: int = 1):
            
        # Randomly determine number of rounds (5-15)
        self.n_rounds = random.randint(2, 10)
        self.n_quadrants = n_quadrants
        self.n_queues = n_queues
        self.max_cues_per_round = n_quadrants * n_queues
        
        # Setup quadrants and queues
        self.letters = [chr(65 + i) for i in range(n_quadrants * n_queues)]
        self.queue_map = {
            q: self.letters[q*n_queues:(q+1)*n_queues]
            for q in range(n_quadrants)
        }
        
        self.quadrants = list(range(n_quadrants))
        self.biased_quadrant = random.choice(self.quadrants)
        debug_log(f"Created VSTtask with biased quadrant: {self.biased_quadrant} and {self.n_rounds} rounds")
        self.rounds = self._generate_rounds()

    def _get_color(self, quadrant: int) -> str:
        if quadrant == self.biased_quadrant:
            return 'RED' if random.random() < 0.9 else 'GREEN'
        return random.choice(['RED', 'GREEN'])

    def _generate_rounds(self):
        max_attempts = 100  # Prevent infinite loops
        attempt = 0
        
        while attempt < max_attempts:
            rounds = []
            for _ in range(self.n_rounds):
                # Determine number of active cues for this round (2 to max)
                n_active_cues = random.randint(2, self.max_cues_per_round)
                
                # Create all possible cues first
                all_cues = []
                for q in self.quadrants:
                    for queue in self.queue_map[q]:
                        all_cues.append({
                            'name': queue,
                            'color': self._get_color(q),
                            'quadrant': q,
                            'active': False  # Default to inactive
                        })
                
                # Randomly select cues to be active
                active_indices = random.sample(range(len(all_cues)), n_active_cues)
                for idx in active_indices:
                    all_cues[idx]['active'] = True
                
                rounds.append({'cues': all_cues})
            
            # Validate the rounds
            if self._validate_rounds([r['cues'] for r in rounds]):
                debug_log(f"Generated {len(rounds)} rounds successfully after {attempt + 1} attempts")
                return rounds
            
            attempt += 1
        
        # If we can't generate valid rounds after max_attempts, return what we have
        debug_log(f"Warning: Could not generate valid rounds after {max_attempts} attempts, using last attempt")
        return rounds

    def _validate_rounds(self, rounds):
        color_counts = {q: {'RED': 0, 'GREEN': 0} for q in self.quadrants}
        for round_queues in rounds:
            for queue in round_queues:
                if queue['active']:  # Only count active queues
                    q = queue['quadrant']
                    color = queue['color']
                    color_counts[q][color] += 1
        
        for q in self.quadrants:
            total = color_counts[q]['RED'] + color_counts[q]['GREEN']
            if total == 0:
                return False
            red_ratio = color_counts[q]['RED'] / total
            if q == self.biased_quadrant:
                
                if red_ratio < 0.8:
                    return False
            elif not (0.35 <= red_ratio <= 0.65):
                return False
        return True
    
    def get_round_data(self, round_num: int):
        return self.rounds[round_num]


class VSTtaskEasy(VSTtask):
    """Easy mode: No occlusions (all buttons always active) but keeps validation"""
    
    def __init__(self, n_quadrants: int = 4, n_queues: int = 1):
        super().__init__(n_quadrants, n_queues)
        self.n_rounds = random.randint(5, 15)
        debug_log(f"Created VSTtaskEasy with biased quadrant: {self.biased_quadrant} and {self.n_rounds} rounds")
    
    def _generate_rounds(self):
        max_attempts = 100  # Prevent infinite loops
        attempt = 0
        
        while attempt < max_attempts:
            rounds = []
            for _ in range(self.n_rounds):
                # Create all possible cues - ALL ACTIVE in easy mode
                all_cues = []
                for q in self.quadrants:
                    for queue in self.queue_map[q]:
                        all_cues.append({
                            'name': queue,
                            'color': self._get_color(q),
                            'quadrant': q,
                            'active': True  # Always active in easy mode
                        })
                
                rounds.append({'cues': all_cues})
            
            # Validate the rounds (keeps validation for solvability)
            if self._validate_rounds([r['cues'] for r in rounds]):
                debug_log(f"Generated {len(rounds)} easy mode rounds successfully after {attempt + 1} attempts")
                return rounds
            
            attempt += 1
        
        # If we can't generate valid rounds after max_attempts, return what we have
        debug_log(f"Warning: Could not generate valid easy mode rounds after {max_attempts} attempts, using last attempt")
        return rounds
    
class VSTtaskHard(VSTtask):
    """Hard mode: Has occlusions but NO validation (weather prediction style)"""
    
    def __init__(self, n_quadrants: int = 4, n_queues: int = 1):
        super().__init__(n_quadrants, n_queues)
        self.n_rounds = random.randint(1, 15)
        debug_log(f"Created VSTtaskHard with biased quadrant: {self.biased_quadrant} and {self.n_rounds} rounds")
    
    def _generate_rounds(self):
        # No validation loop - just generate rounds directly
        rounds = []
        for _ in range(self.n_rounds):
            # Determine number of active cues for this round (2 to max)
            n_active_cues = random.randint(1, self.max_cues_per_round)
            
            # Create all possible cues first
            all_cues = []
            for q in self.quadrants:
                for queue in self.queue_map[q]:
                    all_cues.append({
                        'name': queue,
                        'color': self._get_color(q),
                        'quadrant': q,
                        'active': False  # Default to inactive
                    })
            
            # Randomly select cues to be active
            active_indices = random.sample(range(len(all_cues)), n_active_cues)
            for idx in active_indices:
                all_cues[idx]['active'] = True
            
            rounds.append({'cues': all_cues})
        
        debug_log(f"Generated {len(rounds)} hard mode rounds (no validation)")
        return rounds
    
    
