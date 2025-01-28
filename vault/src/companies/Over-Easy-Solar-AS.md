```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Over-Easy-Solar-AS" or company = "Over Easy Solar AS")
sort location, dt_announce desc
```
