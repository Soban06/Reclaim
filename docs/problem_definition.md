# Problem definition

Reclaim is an approved Track A project. Its intended users are e-commerce operations managers, inventory planners and customer-experience staff. It estimates product-return risk to support planning and helpful intervention.

The first dataset supports a binary label on a customer-product purchase event: `isReturned = 1` for returned and `0` for kept. It has no basket/order identifier, so whole-order return prediction is outside the current implementation.

The intended production prediction time is order placement. Inputs must be available by then. Exact price, discount, past customer behavior and shipping context are desired inputs; the current dataset only partially supports them.

Machine learning is justified by potentially interacting signals across product type, brand and customer context. It must still demonstrate improvement over majority and simple rule baselines. No trained model or measured predictive advantage is claimed in Deliverable 1.

Success for this milestone means a reproducible, documented pipeline from original data to an audited development table, isolated training/validation preprocessing, exploratory charts and a LaTeX report. Later success requires a hosted UI and model backend, meaningful evaluation and understandable outputs.
