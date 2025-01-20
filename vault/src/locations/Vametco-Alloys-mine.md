```dataview
table company, tech, component, status, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and location = "Vametco Alloys mine"
sort company, dt_announce desc
```
