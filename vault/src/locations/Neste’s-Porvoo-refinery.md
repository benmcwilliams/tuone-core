```dataview
table company, tech, component, status, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and location = "Neste’s Porvoo refinery"
sort company, dt_announce desc
```
