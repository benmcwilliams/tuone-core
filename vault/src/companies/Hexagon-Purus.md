```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Hexagon-Purus" or company = "Hexagon Purus")
sort location, dt_announce desc
```
