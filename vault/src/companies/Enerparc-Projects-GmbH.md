```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Enerparc-Projects-GmbH" or company = "Enerparc Projects GmbH")
sort location, dt_announce desc
```
