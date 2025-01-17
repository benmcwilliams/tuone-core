```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "SK Hi Tech Battery Materials Poland sp. z o.o."
sort location, dt_announce desc
```
