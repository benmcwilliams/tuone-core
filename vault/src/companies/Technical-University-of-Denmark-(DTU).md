```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Technical-University-of-Denmark-(DTU)" or company = "Technical University of Denmark (DTU)")
sort location, dt_announce desc
```
