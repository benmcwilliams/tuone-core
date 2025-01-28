```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Solar-Visuals" or company = "Solar Visuals")
sort location, dt_announce desc
```
