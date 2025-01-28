```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Solar-Italy-3-Srl" or company = "Solar Italy 3 Srl")
sort location, dt_announce desc
```
