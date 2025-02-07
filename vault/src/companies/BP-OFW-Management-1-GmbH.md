```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "BP-OFW-Management-1-GmbH" or company = "BP OFW Management 1 GmbH")
sort location, dt_announce desc
```
