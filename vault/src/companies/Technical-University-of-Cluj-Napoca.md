```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Technical-University-of-Cluj-Napoca" or company = "Technical University of Cluj Napoca")
sort location, dt_announce desc
```
