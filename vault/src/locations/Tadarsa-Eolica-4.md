```dataview
table company, tech, component, status, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and location = "Tadarsa Eolica 4"
sort company, dt_announce desc
```
