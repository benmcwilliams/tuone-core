```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Nomikos-A.B.E.K." or company = "Nomikos A.B.E.K.")
sort location, dt_announce desc
```
