```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Landshut-University-of-Applied-Sciences" or company = "Landshut University of Applied Sciences")
sort location, dt_announce desc
```
