```dataview
table company, tech, component, status, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and location = "Las Palmas de Gran Canaria"
sort company, dt_announce desc
```
