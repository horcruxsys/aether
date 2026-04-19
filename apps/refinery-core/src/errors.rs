use thiserror::Error;
use tonic::Status;

#[derive(Error, Debug)]
pub enum AetherError {
    #[error("Database constraint or connectivity error: {0}")]
    DatabaseError(#[from] sqlx::Error),

    #[error("Semantic parsing error: {0}")]
    SemanticError(String),

    #[error("File system IO error: {0}")]
    IoError(#[from] std::io::Error),

    #[error("Avro encoding/decoding error: {0}")]
    AvroError(#[from] apache_avro::Error),

    #[error("Internal processing error: {0}")]
    InternalError(#[from] anyhow::Error),

    #[error("gRPC Transport Error: {0}")]
    TransportError(#[from] tonic::transport::Error),
}

// Ensure our canonical errors instantly map back into gRPC status bounds for seamless client error interpretation
impl From<AetherError> for Status {
    fn from(err: AetherError) -> Self {
        match err {
            AetherError::DatabaseError(e) => Status::internal(format!("DB ERROR: {}", e)),
            AetherError::SemanticError(s) => Status::invalid_argument(s),
            AetherError::IoError(e) => Status::internal(format!("IO ERROR: {}", e)),
            AetherError::AvroError(e) => Status::internal(format!("AVRO ERROR: {}", e)),
            AetherError::InternalError(e) => Status::internal(format!("INTERNAL ERROR: {}", e)),
            AetherError::TransportError(e) => Status::internal(format!("TRANSPORT ERROR: {}", e)),
        }
    }
}
