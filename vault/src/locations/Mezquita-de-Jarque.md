```dataview
table company, tech, component, status, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and location = "Mezquita de Jarque"
sort company, dt_announce desc
```
