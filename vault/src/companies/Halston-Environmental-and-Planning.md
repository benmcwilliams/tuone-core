```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Halston-Environmental-and-Planning" or company = "Halston Environmental and Planning")
sort location, dt_announce desc
```
