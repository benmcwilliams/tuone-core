```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Eco-Tec" or company = "Eco Tec")
sort location, dt_announce desc
```
