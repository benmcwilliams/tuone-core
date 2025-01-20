```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and company = "AGH University of Science and Technology"
sort location, dt_announce desc
```
