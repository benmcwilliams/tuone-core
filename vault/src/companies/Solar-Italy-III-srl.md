```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Solar-Italy-III-srl" or company = "Solar Italy III srl")
sort location, dt_announce desc
```
