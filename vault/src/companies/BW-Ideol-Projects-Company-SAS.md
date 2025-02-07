```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "BW-Ideol-Projects-Company-SAS" or company = "BW Ideol Projects Company SAS")
sort location, dt_announce desc
```
