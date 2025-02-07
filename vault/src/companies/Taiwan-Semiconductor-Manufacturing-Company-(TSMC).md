```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Taiwan-Semiconductor-Manufacturing-Company-(TSMC)" or company = "Taiwan Semiconductor Manufacturing Company (TSMC)")
sort location, dt_announce desc
```
