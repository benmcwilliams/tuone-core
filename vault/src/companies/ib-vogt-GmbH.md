```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "ib-vogt-GmbH" or company = "ib vogt GmbH")
sort location, dt_announce desc
```
