import random
from .config import debug_log

class VSTtask:
    def __init__(self, n_rounds: int = 5, n_quadrants: int = 4, n_queues: int = 1):
        if not 2 <= n_quadrants <= 4:
            raise ValueError("Number of quadrants must be between 2 and 4")
        if n_queues < 1:
            raise ValueError("Number of queues per quadrant must be at least 1")
            
        self.n_rounds = n_rounds
        self.n_quadrants = n_quadrants
        self.n_queues = n_queues
        
        # Setup quadrants and queues
        self.letters = [chr(65 + i) for i in range(n_quadrants * n_queues)]
        self.queue_map = {
            q: self.letters[q*n_queues:(q+1)*n_queues]
            for q in range(n_quadrants)
        }
        
        self.quadrants = list(range(n_quadrants))
        self.biased_quadrant = random.choice(self.quadrants)
        debug_log(f"Created VSTtask with biased quadrant: {self.biased_quadrant}")
        self.rounds = self._generate_rounds()

    def _get_color(self, quadrant: int) -> str:
        if quadrant == self.biased_quadrant:
            return 'RED' if random.random() < 0.9 else 'GREEN'
        return random.choice(['RED', 'GREEN'])

    def _generate_rounds(self):
        while True:
            rounds = []
            for _ in range(self.n_rounds):
                round_queues = []
                for q in self.quadrants:
                    for queue in self.queue_map[q]:
                        round_queues.append({
                            'name': queue,
                            'color': self._get_color(q),
                            'quadrant': q
                        })
                rounds.append({'queues': round_queues})
            if self._validate_rounds([r['queues'] for r in rounds]):
                return rounds

    def _validate_rounds(self, rounds):
        color_counts = {q: {'RED': 0, 'GREEN': 0} for q in self.quadrants}
        for round_queues in rounds:
            for queue in round_queues:
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
    
    def get_task_description(self) -> str:
        return (
            f"You will play a game with {self.n_rounds} rounds.<br>"
            "In each round you'll see active queues (clickable buttons):<br>"
            "One quadrant has 90% one color / 10% the other<br>"
            "Other quadrants have a 50/50 color distribution<br>"
            "At least one queue is active per round<br>"
            "Active queues disappear after a short duration.<br><br>"
            f"After {self.n_rounds} rounds, identify the biased quadrant.<br>"
            "Correct: +100 points, Wrong: -100 points."
        )